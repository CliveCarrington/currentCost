#!/bin/bash

#### Checks whether an application is running
checkFile="ccDataReceiver.py"

status=`/bin/ps -ef | grep $checkFile  | wc -l`

echo `date` "Checking $checkFile"
echo "Status = $status"

/bin/ps -ef | grep $checkFile

if [ $status -eq "1" ]
then
	echo "Need to start"
	python $checkFile >> ../log/currentCost.log&

fi
 
