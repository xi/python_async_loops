#!/bin/bash
while true; do
    sleep $(($RANDOM % 5))
    echo $RANDOM
done
