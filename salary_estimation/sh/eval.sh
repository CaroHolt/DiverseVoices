source /lustre/project/ki-topml/minbui/.bashrc
conda_initialize
micromamba activate audio

python /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/scripts/eval_implicit.py >> output.txt

python /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/scripts/eval_implicit.py \
    --input_folder /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/implicit_explicit \
    --output_folder /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/implicit_explicit/eval >> output.txt


python /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/scripts/eval_implicit.py \
    --input_folder /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/implicit_explicit_black \
    --output_folder /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/implicit_explicit_black/eval >> output.txt