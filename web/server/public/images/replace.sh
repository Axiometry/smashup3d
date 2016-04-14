#!/bin/sh

files=`find *`
while read -r f; do
	f2=`echo $f | tr '[:upper:]' '[:lower:]' | sed "s/[ _]//g"`
	echo "$f -> $f2"
	mv "$f" "$f2"
done <<< "$files"


