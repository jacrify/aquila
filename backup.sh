cd ~/klipper_config
mv printer-* oldconfigs/
git add .
git commit -m "backup"
git push -u origin master
