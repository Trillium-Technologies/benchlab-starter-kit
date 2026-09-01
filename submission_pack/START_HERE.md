# Start here

1. Read [`PARTICIPANT_CONTRACT.md`](../PARTICIPANT_CONTRACT.md) before editing the template.

2. Run the supplied example unchanged:

   ```bash
   cd local_tests
   ./test_local.sh 20261111T060000Z

3. Do not start adapting the package until the example passes locally.

   Adapt `submission_pack/' to your own forecasting workflow:
     - replace the example model.py or equivalent forecasting logic
     - add your dependencies and required model assets
     - configure submission.json;
     - document your submitted workflow in README.md

5. Test the complete workflow locally again with local_tests/test_local.sh. Repeat this throughout development.
