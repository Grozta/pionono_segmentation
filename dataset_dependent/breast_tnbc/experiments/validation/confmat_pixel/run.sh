python src/main.py -c ../../experiments/breast_tnbc/experiments/validation/confmat_pixel/base_config.yaml -dc ../../experiments/breast_tnbc/data_configs/data_config_val0.yaml -ef ../../experiments/breast_tnbc/experiments/validation/confmat_pixel/cval0
python src/main.py -c ../../experiments/breast_tnbc/experiments/validation/confmat_pixel/base_config.yaml -dc ../../experiments/breast_tnbc/data_configs/data_config_val0.yaml -ef ../../experiments/breast_tnbc/experiments/validation/confmat_pixel/cval1
python src/main.py -c ../../experiments/breast_tnbc/experiments/validation/confmat_pixel/base_config.yaml -dc ../../experiments/breast_tnbc/data_configs/data_config_val0.yaml -ef ../../experiments/breast_tnbc/experiments/validation/confmat_pixel/cval2
python src/main.py -c ../../experiments/breast_tnbc/experiments/validation/confmat_pixel/base_config.yaml -dc ../../experiments/breast_tnbc/data_configs/data_config_val0.yaml -ef ../../experiments/breast_tnbc/experiments/validation/confmat_pixel/cval3

python src/postprocessing_tools/calculate_results.py -e ../../experiments/breast_tnbc/experiments/validation/confmat_pixel/