# Read-Only Commands

Use these as inspection templates. Explain what each command does before asking the user
to run it. Avoid expensive full scans on very large collections unless an approved runbook
requires them.

## Open a production Rails console

Prefer an ephemeral Rails console pod over execing into a live serving pod:

```bash
kubectl run <YOUR-NAME>-rails-api --rm -it --restart=Never -n leadgenie \
  --image=nginx:latest \
  --overrides="$(kubectl get deployment rails-api -n leadgenie -o json | jq '.spec.template.spec | {spec:{serviceAccountName: "rails",serviceAccount: "rails", containers: [{name: "rails-api", image: .containers[0].image, env: .containers[0].env, volumeMounts: .containers[0].volumeMounts, command:["./bin/rails", "console"], stdin: true, stdinOnce: true, tty: true}], volumes: .volumes}}')"
```

## Model, collection, database, cluster

Run inside Rails console:

```ruby
model = LoginAttempt
{
  database_name: model.database_name,
  collection_name: model.collection.name,
  cluster: model.collection.cluster,
  indexes: model.collection.indexes.to_a.map { |idx| idx.slice("name", "key", "unique", "sparse", "partialFilterExpression", "expireAfterSeconds") }
}
```

## Size checks

Prefer estimated count for large collections:

```ruby
LoginAttempt.estimated_count
```

Use exact `count` only when the collection is known small or the runbook explicitly calls
for it:

```ruby
LoginAttempt.count
```

## Index existence

```ruby
LoginAttempt.collection.indexes.to_a.map { |idx| [idx["name"], idx["key"]] }
```

## Current index builds

If `mongosh` is available and the user has the right access:

```javascript
db.currentOp({ "command.createIndexes": { $exists: true } }).inprog
```

If Rails utilities are available, follow the current DevOps runbook for index status
commands. Treat status checks as read-only.
