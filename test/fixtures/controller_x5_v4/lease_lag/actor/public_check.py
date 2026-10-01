from leases import run
assert run({"lease":{"owner":"east","until":100,"token":1},"operations":[{"op":"renew","owner":"east","worker_now":90,"server_now":90,"ttl":20}]}) == {"results":[{"status":"renewed","token":1}],"lease":{"owner":"east","until":110,"token":1}}
