from securesystemslib.interface import (generate_and_write_rsa_keypair,
    import_rsa_privatekey_from_file)
from in_toto.models.layout import Layout, Step, Inspection
from in_toto.models.metadata import Metablock

def main():
    alice_path = generate_and_write_rsa_keypair(password="123", filepath="alice")
    alice_key = import_rsa_privatekey_from_file(alice_path, password="123")

    bob_path = generate_and_write_rsa_keypair(password="123", filepath="bob")
    carl_path = generate_and_write_rsa_keypair(password="123", filepath="carl")

    layout = Layout()

    bob_pubkey = layout.add_functionary_key_from_path(bob_path + ".pub")
    carl_pubkey = layout.add_functionary_key_from_path(carl_path + ".pub")

    layout.set_relative_expiration(months=1)




    step_clone = Step(name="clone")
    step_clone.pubkeys = [bob_pubkey["keyid"]]

    step_clone.set_expected_command_from_string(
         "/bin/sh -c \"git clone ${GITHUB_REPOSITORY} && cd ${${GITHUB_REPOSITORY#*/}%.git} && git reset --hard ${GITHUB_SHA}\"")

    step_clone.add_product_rule_from_string("ALLOW *")
    step_clone.add_product_rule_from_string("DISALLOW *")






    step_build = Step(name="build")
    step_build.pubkeys = [carl_pubkey["keyid"]]
    step_build.set_expected_command_from_string("go build -o build/sample \"${${GITHUB_REPOSITORY#*/}%.git}/main.go\"")

    step_build.add_material_rule_from_string("MATCH ${${GITHUB_REPOSITORY#*/}%.git}/* WITH PRODUCTS FROM clone")
    step_build.add_material_rule_from_string("DISALLOW *")

    step_build.add_product_rule_from_string("CREATE build/sample")
    step_build.add_product_rule_from_string("DISALLOW *")




    step_build = Step(name="docker_build")
    step_build.pubkeys = [carl_pubkey["keyid"]]
    step_build.set_expected_command_from_string("docker build --tag ${DOCKER_TAG} --file Dockerfile ${${GITHUB_REPOSITORY#*/}%.git}/ && docker save -o img.tar")

    step_build.add_material_rule_from_string("MATCH ${${GITHUB_REPOSITORY#*/}%.git}/* WITH PRODUCTS FROM clone")
    step_build.add_material_rule_from_string("DISALLOW *")

    step_build.add_product_rule_from_string("CREATE img.tar")
    step_build.add_product_rule_from_string("DISALLOW *")





    step_sbom_gen = Step(name="sbom_gen")
    step_sbom_gen.pubkeys = [bob_pubkey["keyid"]]
    step_sbom_gen.set_expected_command_from_string("syft packages docker-archive:img.tar -o cyclonedx-json > sbom.json")

    step_sbom_gen.add_material_rule_from_string("MATCH img.tar WITH PRODUCTS FROM build")
    step_sbom_gen.add_material_rule_from_string("DISALLOW *")

    step_sbom_gen.add_product_rule_from_string("CREATE sbom.json")
    step_sbom_gen.add_product_rule_from_string("DISALLOW *")





    step_docker_push = Step(name="docker_push")
    step_docker_push.pubkeys = [bob_pubkey["keyid"]]
    step_docker_push.set_expected_command_from_string("docker push ${DOCKER_TAG}")

    step_docker_push.add_material_rule_from_string("DISALLOW *")

    step_docker_push.add_product_rule_from_string("DISALLOW *")





    step_oci_sign = Step(name="oci_sign")
    step_oci_sign.pubkeys = [bob_pubkey["keyid"]]
    step_oci_sign.set_expected_command_from_string("cosign sign ${DOCKER_TAG} --key cosign.key --upload=false --output-signature=./sig")

    step_oci_sign.add_material_rule_from_string("DISALLOW *")

    step_oci_sign.add_product_rule_from_string("CREATE ./sig")




    inspection = Inspection(name="check_artifacts")
    inspection.add_material_rule_from_string("MATCH ../build/sample WITH PRODUCTS FROM build")
    inspection.add_material_rule_from_string("MATCH ../sbom.json WITH PRODUCTS FROM sbom_gen")
    inspection.add_material_rule_from_string("MATCH ../sig WITH PRODUCTS FROM oci_sign")

    metablock = Metablock(signed=layout)
    metablock.sign(alice_key)
    metablock.dump("root.layout")

if __name__ == '__main__':
    main()

