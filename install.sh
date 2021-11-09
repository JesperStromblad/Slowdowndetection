#!/bin/bash


# Function to check commands
function checkCommand(){
        _=$(command -v $1);
        if [ "$?" != "0" ]; then
                echo $?
                printf -- '\033[31m ERROR: You dont seem to have %s installed \033[0m\n';
                exit 127;
        fi;
}

checkCommand virtualenv
checkCommand git
checkCommand pip

## Setting up virtual environment
echo "Setting up virtual environment"
virtualenv venv --python=python3.7.0
source venv/bin/activate

pip install -r requirements.txt

