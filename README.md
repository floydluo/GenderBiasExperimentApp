# Experimental Quiz App for Gender Bias Identification

```shell


git clone https://github.com/floydluo/GenderBiasExperimentApp.git
cd GenderBiasExperimentApp

# install miniconda
# https://docs.conda.io/en/latest/miniconda.html
# 

conda create -n gb python=3.7

conda activate gb
pip install -r requirements.txt
pip install flask_bootstrap


# export FLASK_DEBUG=1 # only for debugging the code
export FLASK_APP=main.py


## datebase issue
flask db init
flask db migrate -m'initial migration'
flask db upgrade


# flask run
flask run --host 0.0.0.0 # under the same wifi, other people can visit it.

# install sqlite db
# https://sqlitebrowser.org/

```
