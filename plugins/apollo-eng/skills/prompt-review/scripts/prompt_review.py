"""Evidence-bound advisory prompt checks. No model/provider or application calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.exceptions import NoSuchResource


def obj(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required}


STRING = {"type": "string", "minLength": 1}
STRINGS = {"type": "array", "items": STRING, "uniqueItems": True}
BOOL = {"type": "boolean"}
SCHEMA = {"type": ["object", "boolean"]}
GAP = obj({"code": STRING, "prompt_id": STRING, "message": STRING, "required": BOOL})
TOOL = obj({"name": STRING, "input_schema": SCHEMA,
            "output_schema": {"type": ["object", "boolean", "null"]},
            "requires": STRINGS, "capabilities": STRINGS, "side_effect": BOOL},
           ["name", "input_schema"])
CALL = obj({"name": STRING, "arguments": {"type": "object"},
            "source_quote": STRING, "result_fields": STRINGS,
            "sequence_id": STRING}, ["name", "arguments", "source_quote"])
VARIANT = obj({
    "id": STRING,
    "messages": {"type": "array", "minItems": 1, "items": obj({
        "role": {"enum": ["system", "developer", "user", "assistant", "tool"]},
        "content": {"type": "string"}})},
    "tools": {"type": "array", "items": TOOL}, "tools_complete": BOOL,
    "output_schema": {"type": ["object", "boolean", "null"]},
    "output_examples": {"type": "array", "items": obj({"value": {}, "source_quote": STRING})},
    "call_examples": {"type": "array", "items": CALL},
    "required_variables": STRINGS, "provided_variables": STRINGS, "deferred_variables": STRINGS,
})
BUNDLE_SCHEMA = obj({
    "version": {"const": 1},
    "repository": {"enum": ["data-platform", "leadgenie", "claude-plugins"]},
    "base_sha": {"type": "string", "pattern": "^[a-f0-9]{40}$"},
    "head_sha": {"type": "string", "pattern": "^[a-f0-9]{40}$"},
    "sources": {"type": "array", "items": obj({"path": STRING,
        "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "content": {"type": "string"}})},
    "changed_paths": STRINGS,
    "prompts": {"type": "array", "items": obj({"id": STRING, "source_path": STRING,
        "dependencies": STRINGS, "variants": {"type": "array", "minItems": 1, "items": VARIANT}})},
    "coverage_gaps": {"type": "array", "items": GAP}, "discovery_complete": BOOL,
})
FINDING = obj({"rule_id": STRING, "prompt_id": STRING, "variant_id": STRING,
    "severity": {"enum": ["critical", "high", "medium", "low"]},
    "message": STRING, "evidence_quote": STRING, "recommendation": STRING,
    "regression_test": STRING})
SEMANTIC_SCHEMA = obj({"version": {"const": 1},
    "bundle_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
    "findings": {"type": "array", "items": FINDING},
    "coverage_gaps": {"type": "array", "items": GAP}})
# Reviewer protocol is closed: an unknown status/error channel must not be
# silently discarded while empty findings are interpreted as success.
SEMANTIC_SCHEMA["additionalProperties"] = False
FINDING["additionalProperties"] = False
SEMANTIC_SCHEMA["properties"]["coverage_gaps"]["items"] = {**GAP, "additionalProperties": False}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode("utf-8")).hexdigest()


def validate(value, schema):
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(list(e.path)))
    if errors:
        # Never copy a potentially sensitive complete invalid instance into logs.
        error = errors[0]
        raise ValueError("Invalid contract at " + "/".join(map(str, error.path)) +
                         ": " + error.validator)


def valid_local_schema(schema):
    """Disallow network schema resolution, including references nested in definitions."""
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key in ("$ref", "$dynamicRef") and (not isinstance(value, str) or not value.startswith("#")):
                raise ValueError("External schema references are unavailable offline")
            valid_local_schema(value)
    elif isinstance(schema, list):
        for value in schema:
            valid_local_schema(value)


def check_local_schema(schema):
    valid_local_schema(schema)
    Draft202012Validator.check_schema(schema)


def unavailable_schema_resource(uri):
    raise NoSuchResource(ref=uri)


def schema_errors(schema, value):
    check_local_schema(schema)
    # Defense in depth: even a fragment ref whose nested $id changes its base
    # URI must never fall back to jsonschema's remote retrieval behavior.
    return list(Draft202012Validator(schema, registry=Registry(retrieve=unavailable_schema_resource)).iter_errors(value))


def field_exists(schema, path):
    """True/False/None: declared, impossible under closed schema, or unknown."""
    for part in path.split("."):
        if not isinstance(schema, dict):
            return None
        if any(k in schema for k in ("$ref", "oneOf", "anyOf", "allOf")):
            return None
        if part not in schema.get("properties", {}):
            if "patternProperties" in schema:
                return None  # Pattern-defined fields need actual result validation.
            return False if schema.get("additionalProperties") is False else None
        schema = schema["properties"][part]
    return schema is not False


def evidence_text(bundle, prompt, variant):
    paths = set(prompt["dependencies"]) | {prompt["source_path"]}
    return "\n".join([m["content"] for m in variant["messages"]] +
                     [s["content"] for s in bundle["sources"] if s["path"] in paths])


def validate_labeled_example(example, kind):
    """A literal labeled example must agree with the adapter's structured value."""
    match = re.fullmatch(r"```" + re.escape(kind) + r"\s*\n(.*?)\n```", example["source_quote"], re.S)
    if not match:
        return  # Prose examples remain an adapter/semantic-review responsibility.
    try:
        value = json.loads(match.group(1))
    except ValueError:
        raise ValueError("Labeled example is not valid JSON") from None
    if kind == "tool-call":
        if not isinstance(value, dict) or "name" not in value or "arguments" not in value:
            raise ValueError("Labeled tool example has no call contract")
        actual = {key: value[key] for key in ("name", "arguments")}
        expected = {key: example[key] for key in ("name", "arguments")}
    else:
        actual, expected = value, example["value"]
    if digest(actual) != digest(expected):
        raise ValueError("Structured example differs from its source quote")


def locate(bundle, prompt, quote):
    for source in bundle["sources"]:
        if source["path"] not in set(prompt["dependencies"]) | {prompt["source_path"]}:
            continue
        offset = source["content"].find(quote)
        if offset >= 0:
            return {"path": source["path"], "line": source["content"][:offset].count("\n") + 1}
    return {"path": prompt["source_path"], "line": None, "location": "assembled-variant"}


def review_bundle(bundle, semantic=None):
    result = {"version": 1, "repository": None, "head_sha": None, "bundle_sha256": digest(bundle),
              "coverage_status": "error", "findings": [], "coverage_gaps": [],
              "decision": "error", "enforcement": "advisory", "enabled_blocking_rules": []}
    try:
        validate(bundle, BUNDLE_SCHEMA)
        result.update(repository=bundle["repository"], head_sha=bundle["head_sha"])
        source_paths = [s["path"] for s in bundle["sources"]]
        if len(source_paths) != len(set(source_paths)):
            raise ValueError("Duplicate source paths")
        for source in bundle["sources"]:
            if hashlib.sha256(source["content"].encode("utf-8")).hexdigest() != source["sha256"]:
                raise ValueError("Source digest mismatch")
        ids = [p["id"] for p in bundle["prompts"]]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate prompt IDs")
        gaps = list(bundle["coverage_gaps"])
        findings = result["findings"]

        def gap(code, prompt_id, message):
            gaps.append({"code": code, "prompt_id": prompt_id, "message": message, "required": True})

        if not bundle["discovery_complete"]:
            gap("discovery-incomplete", "bundle", "Affected prompt inventory is not complete")

        for prompt in bundle["prompts"]:
            variants = [v["id"] for v in prompt["variants"]]
            if len(variants) != len(set(variants)):
                raise ValueError("Duplicate variant IDs")
            if any(p not in source_paths for p in set(prompt["dependencies"]) | {prompt["source_path"]}):
                gap("dependency-source-missing", prompt["id"], "A declared source dependency is unavailable")
            for variant in prompt["variants"]:
                text = evidence_text(bundle, prompt, variant)

                def finding(rule, message, quote, fix, severity="high"):
                    if quote not in text or not quote:
                        raise ValueError("Ungrounded structured example")
                    findings.append({"rule_id": rule, "prompt_id": prompt["id"],
                        "variant_id": variant["id"], "severity": severity, "message": message,
                        "evidence_quote": quote, "recommendation": fix,
                        "regression_test": "prompt-review/" + rule,
                        "method": "deterministic", "blocking": False,
                        "source": locate(bundle, prompt, quote)})

                names = [t["name"] for t in variant["tools"]]
                if len(names) != len(set(names)):
                    raise ValueError("Duplicate tool names in active variant")
                tools = {t["name"]: t for t in variant["tools"]}
                # Declared contracts are checked even if the prompt has no examples.
                # Otherwise an invalid schema can silently produce a complete pass.
                declared_schemas = [("invalid-tool-schema", t["input_schema"]) for t in variant["tools"]]
                declared_schemas += [("invalid-tool-schema", t["output_schema"]) for t in variant["tools"] if t.get("output_schema") is not None]
                if variant["output_schema"] is not None:
                    declared_schemas.append(("invalid-output-schema", variant["output_schema"]))
                for code, schema in declared_schemas:
                    try:
                        check_local_schema(schema)
                    except Exception as exc:
                        gap(code, prompt["id"], "Declared schema cannot be validated: " + type(exc).__name__)
                if not variant["tools_complete"]:
                    gap("tool-bindings-unavailable", prompt["id"], "Active tool inventory is not authoritative")
                missing = set(variant["required_variables"]) - set(variant["provided_variables"]) - set(variant["deferred_variables"])
                for name in sorted(missing):
                    # A missing renderer input is an incomplete check, not an invented prompt defect.
                    gap("missing-variable", prompt["id"], "Required renderer variable unavailable: " + name)

                # Only strict STEP headings/references are deterministic. Lettered cases,
                # conditional headings, and semantic destination mismatches go to the reviewer.
                assembled = "\n".join(m["content"] for m in variant["messages"])
                headings = set()
                prose = []
                fence = None
                for line in assembled.splitlines():
                    marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
                    if fence:
                        if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= fence[1] and not marker.group(2).strip():
                            fence = None
                        continue
                    if marker:
                        fence = (marker.group(1)[0], len(marker.group(1)))
                        continue
                    match = re.match(r"^#{1,6}\s+(?:\*\*)?STEP\s+(\d+(?:\.\d+)*[A-Za-z]?)\b", line, re.I)
                    if match:
                        headings.add(match.group(1).upper())
                    else:
                        prose.append(line)
                if headings:
                    for line in prose:
                        for ref in re.finditer(r"\bSTEP\s+(\d+(?:\.\d+)*[A-Za-z]?)\b", line, re.I):
                            if ref.group(1).upper() not in headings:
                                composition_unknown = any(g["required"] and g["prompt_id"] in (prompt["id"], "bundle") and
                                    g["code"] in {"runtime-composition-unavailable", "dependency-source-missing", "dependency-target-missing", "missing-variable"}
                                    for g in gaps)
                                if composition_unknown:
                                    gap("section-resolution-unverified", prompt["id"], "A STEP reference cannot be resolved without complete composition")
                                else:
                                    finding("undefined-section", "Reference has no STEP heading in the assembled prompt", line.strip(),
                                            "Correct the reference or include the missing section; preserve the intended destination.")

                seen = {}
                for call in variant["call_examples"]:
                    if call["source_quote"] not in text:
                        raise ValueError("Call example is not grounded in reviewed source")
                    validate_labeled_example(call, "tool-call")
                    tool = tools.get(call["name"])
                    if tool is None:
                        if variant["tools_complete"]:
                            finding("unavailable-tool", "Illustrated tool is absent from this variant's active inventory", call["source_quote"],
                                    "Use an available tool or correct the runtime registration.")
                        continue
                    try:
                        errors = schema_errors(tool["input_schema"], call["arguments"])
                    except Exception as exc:
                        gap("invalid-tool-schema", prompt["id"], "Tool schema cannot be validated: " + type(exc).__name__)
                    else:
                        if errors:
                            finding("tool-arguments", "Illustrated arguments violate the active input schema (" + errors[0].validator + ")",
                                    call["source_quote"], "Correct the example arguments against the registered schema.")
                    sequence = seen.setdefault(call.get("sequence_id", "default"), set())
                    if set(tool.get("requires", [])) - sequence:
                        finding("tool-prerequisite", "Illustrated sequence omits a declared prerequisite", call["source_quote"],
                                "Call the prerequisite first and preserve the existing downstream tool calls.")
                    sequence.add(call["name"])
                    for field in call.get("result_fields", []):
                        exists = field_exists(tool.get("output_schema"), field)
                        if exists is False:
                            finding("tool-result-field", "Illustrated result field is excluded by the closed output schema: " + field,
                                    call["source_quote"], "Read the declared field or correct the tool output contract.")
                        elif exists is None:
                            gap("result-field-unverified", prompt["id"], "Cannot establish output field: " + field)
                for example in variant["output_examples"]:
                    if example["source_quote"] not in text:
                        raise ValueError("Output example is not grounded in reviewed source")
                    validate_labeled_example(example, "output-example")
                    if variant["output_schema"] is None:
                        gap("example-schema-unavailable", prompt["id"], "Illustrated output cannot be checked without its declared schema")
                        continue
                    try:
                        errors = schema_errors(variant["output_schema"], example["value"])
                    except Exception as exc:
                        gap("invalid-output-schema", prompt["id"], "Output schema cannot be validated: " + type(exc).__name__)
                    else:
                        if errors:
                            finding("output-example", "Illustrated output violates the declared schema (" + errors[0].validator + ")",
                                    example["source_quote"], "Align the example with the output contract and parser.")

        if semantic is not None:
            validate(semantic, SEMANTIC_SCHEMA)
            if semantic["bundle_sha256"] != result["bundle_sha256"]:
                raise ValueError("Semantic review bundle digest mismatch")
            for f in semantic["findings"]:
                prompt = next((p for p in bundle["prompts"] if p["id"] == f["prompt_id"]), None)
                variant = next((v for v in prompt["variants"] if v["id"] == f["variant_id"]), None) if prompt else None
                if not variant or f["evidence_quote"] not in evidence_text(bundle, prompt, variant):
                    raise ValueError("Semantic finding has ungrounded evidence or unknown target")
                findings.append({**f, "method": "semantic", "blocking": False,
                                 "source": locate(bundle, prompt, f["evidence_quote"])})
            gaps.extend(semantic["coverage_gaps"])
        elif bundle["prompts"]:
            gap("semantic-review-not-run", "bundle", "Only deterministic checks ran; semantic review is required for full review")
        # Deduplicate exact findings; never discard different evidence supporting a rule.
        result["findings"] = list({(f["rule_id"], f["prompt_id"], f["variant_id"], f["evidence_quote"]): f for f in findings}.values())
        result["coverage_gaps"] = list({digest(g): g for g in gaps}.values())
        incomplete = any(g["required"] for g in gaps)
        result["coverage_status"] = "incomplete" if incomplete else "complete"
        result["decision"] = "incomplete" if incomplete else ("findings" if findings else "pass")
    except Exception as exc:
        result["error"] = {"type": type(exc).__name__, "message": str(exc) if isinstance(exc, ValueError) else "Invalid review input"}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--semantic-review", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        bundle = json.loads(args.bundle.read_text(encoding="utf-8-sig"))
        semantic = json.loads(args.semantic_review.read_text(encoding="utf-8-sig")) if args.semantic_review else None
        result = review_bundle(bundle, semantic)
    except (OSError, ValueError) as exc:
        result = {"version": 1, "coverage_status": "error", "decision": "error",
                  "findings": [], "coverage_gaps": [], "error": {"type": type(exc).__name__, "message": "Cannot read valid review JSON"}}
    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return {"pass": 0, "findings": 1, "incomplete": 2, "error": 3}[result["decision"]]


if __name__ == "__main__":
    raise SystemExit(main())
