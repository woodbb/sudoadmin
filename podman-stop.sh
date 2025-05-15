#!/bin/sh
 podman stop ldapserver
 podman stop sudoadmin
 podman pod rm sudopod
