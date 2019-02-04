echo nic name:
read nic

apt install -y python3-pip

pip install requests requests-toolbelt


ip address add 172.31.33.22/32 dev $nic
ip address add 172.31.33.118/32 dev $nic
ip address add 172.31.33.229/32 dev $nic
ip address add 172.31.32.244/32 dev $nic
ip address add 172.31.37.223/32 dev $nic
ip address add 172.31.38.78/32 dev $nic
ip address add 172.31.35.107/32 dev $nic
ip address add 172.31.44.42/32 dev $nic
ip address add 172.31.43.169/32 dev $nic
ip address add 172.31.37.41/32 dev $nic
ip address add 172.31.41.39/32 dev $nic
ip address add 172.31.42.132/32 dev $nic
ip address add 172.31.42.196/32 dev $nic
ip address add 172.31.47.17/32 dev $nic
