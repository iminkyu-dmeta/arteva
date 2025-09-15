#!/bin/bash

function command()
{
	local cmd=$1
	echo $cmd
	result=`$cmd`
	echo "$result"

}

while read line
do
	if [[ -n ${line} ]] ; then
		if [[ ${line} =~ ^[0-9] ]] | [[ ${line} =~ ^[#] ]] ; then
			echo "${line}"
		else
			command "${line}"
		fi
	else
		echo
		echo

	fi
	
done < $1
