python src/main.py -c ./dataset_dependent/gleason19/experiments/external_testing/punet/base_config.yaml -dc ./dataset_dependent/gleason19/data_configs/data_config_external_testing.yaml -ef ./dataset_dependent/gleason19/experiments/external_testing/punet/cval0
python src/main.py -c ./dataset_dependent/gleason19/experiments/external_testing/punet/base_config.yaml -dc ./dataset_dependent/gleason19/data_configs/data_config_external_testing.yaml -ef ./dataset_dependent/gleason19/experiments/external_testing/punet/cval1
python src/main.py -c ./dataset_dependent/gleason19/experiments/external_testing/punet/base_config.yaml -dc ./dataset_dependent/gleason19/data_configs/data_config_external_testing.yaml -ef ./dataset_dependent/gleason19/experiments/external_testing/punet/cval2
python src/main.py -c ./dataset_dependent/gleason19/experiments/external_testing/punet/base_config.yaml -dc ./dataset_dependent/gleason19/data_configs/data_config_external_testing.yaml -ef ./dataset_dependent/gleason19/experiments/external_testing/punet/cval3

python src/postprocessing_tools/calculate_results.py -e ./dataset_dependent/gleason19/experiments/external_testing/punet/