from features import run
assert run({"store":{"north":{"search":True}},"operations":[{"op":"lookup","tenant":"north","feature":"search"}]}) == {"results":[{"value":True,"source":"store"}]}
