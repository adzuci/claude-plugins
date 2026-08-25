#!/bin/bash

# Usage: ./fetch-pr-reviews.sh <github-pr-url>
# Example: ./fetch-pr-reviews.sh https://github.com/apolloio/leadgenie/pull/81970
# Also accepts URLs with /files suffix

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <github-pr-url>"
  echo "Example: $0 https://github.com/apolloio/leadgenie/pull/81970"
  exit 1
fi

PR_URL="$1"

# Strip trailing /files, /commits, /checks etc.
PR_URL="${PR_URL%%/files*}"
PR_URL="${PR_URL%%/commits*}"
PR_URL="${PR_URL%%/checks*}"

# Extract owner/repo and PR number from URL
if [[ "$PR_URL" =~ ^https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+)/?$ ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUMBER="${BASH_REMATCH[3]}"
else
  echo "Error: Could not parse PR URL. Expected format: https://github.com/OWNER/REPO/pull/NUMBER"
  exit 1
fi

REPO_SLUG="${OWNER}/${REPO}"
OUTPUT_FILE="/tmp/pr-review-${PR_NUMBER}.md"

echo "Fetching unresolved inline review comments for ${REPO_SLUG}#${PR_NUMBER}..."

# REST API does not expose resolved/unresolved thread state; use GraphQL reviewThreads.
GRAPHQL_QUERY='
query FetchReviewThreads($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          isResolved
          comments(first: 100) {
            nodes {
              author { login }
              body
              path
              line
              originalLine
              createdAt
            }
          }
        }
      }
    }
  }
}'

ALL_THREADS="[]"
AFTER=""

while true; do
  if [[ -n "$AFTER" ]]; then
    PAGE_JSON=$(gh api graphql \
      -f owner="$OWNER" \
      -f name="$REPO" \
      -F number="$PR_NUMBER" \
      -f after="$AFTER" \
      -f query="$GRAPHQL_QUERY")
  else
    PAGE_JSON=$(gh api graphql \
      -f owner="$OWNER" \
      -f name="$REPO" \
      -F number="$PR_NUMBER" \
      -f query="$GRAPHQL_QUERY")
  fi

  PAGE_THREADS=$(echo "$PAGE_JSON" | jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)]')
  ALL_THREADS=$(jq -s 'add' <(echo "$ALL_THREADS") <(echo "$PAGE_THREADS"))

  HAS_NEXT=$(echo "$PAGE_JSON" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
  if [[ "$HAS_NEXT" != "true" ]]; then
    break
  fi
  AFTER=$(echo "$PAGE_JSON" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')
done

# Flatten threads to top-level comment per thread (first comment in each thread).
COMMENTS_JSON=$(echo "$ALL_THREADS" | jq '
  [.[] | .comments.nodes[0] | select(. != null) | {
    path: .path,
    line: (.line // .originalLine // null),
    body: .body,
    user: .author.login,
    created_at: .createdAt
  }]
')

COMMENT_COUNT=$(echo "$COMMENTS_JSON" | jq 'length' 2>/dev/null) || COMMENT_COUNT=0

if [[ "$COMMENT_COUNT" -eq 0 ]]; then
  echo "No unresolved inline review comments found for PR #${PR_NUMBER}."
  exit 0
fi

echo "Found ${COMMENT_COUNT} unresolved inline review comment(s). Generating markdown..."

# Generate the markdown file
{
  echo "# PR #${PR_NUMBER} Review Comments"
  echo ""

  for i in $(seq 0 $((COMMENT_COUNT - 1))); do
    COMMENT=$(echo "$COMMENTS_JSON" | jq ".[$i]")

    PATH_VAL=$(echo "$COMMENT" | jq -r '.path')
    LINE_VAL=$(echo "$COMMENT" | jq -r '.line')
    USER_VAL=$(echo "$COMMENT" | jq -r '.user')
    BODY_VAL=$(echo "$COMMENT" | jq -r '.body')

    FILENAME="$PATH_VAL"

    # Build the location string
    if [[ "$LINE_VAL" != "null" && -n "$LINE_VAL" ]]; then
      LOCATION="${FILENAME}:${LINE_VAL}"
    else
      LOCATION="${FILENAME}"
    fi

    COUNTER=$((i + 1))
    echo "- [ ] **Comment ${COUNTER}** — \`${LOCATION}\` — ${USER_VAL}"
    echo ""
    printf '%s\n' "$BODY_VAL" | sed 's/^/  /'
    echo ""
  done

} > "$OUTPUT_FILE"

echo "Done! Review checklist written to: ${OUTPUT_FILE}"
