#!/bin/bash
# REBUILD - always run this
go build && systemctl restart flow-membrane
echo "membrane: reborn"
