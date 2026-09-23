#!/bin/sh
docoreai init
docoreai start &
exec "$@"
