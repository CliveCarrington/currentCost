#!/bin/bash

cd /home/pi/currentCost/bin

date >> ../log/currentCost.log

echo "Starting Current Cost Capture"
python ccDataReceiver.py >> ../log/currentCost.log&

