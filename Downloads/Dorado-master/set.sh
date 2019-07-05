# set python version to 3.5
printf "\n\n\n -- 开始多拉多配置下载 -- \n\n\n"
alias python='python3'

# use most updated version for pip
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py

# solve unroll issue
git clone https://github.com/Zulko/unroll
cd unroll/unroll/ && python unroll.py && cd ../../

# solve twistted issue
pip install --upgrade incremental
pip install Twisted

printf "\n\n\n 终于，让我们开始下载伟大补丁们！\n\n\n"
pip install python-binance
pip install datetime
rm -rf unroll
rm get-pip.py

printf "\n\n\n如果成功，可以开始写代码了!\n\n\n"

