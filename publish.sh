#!/bin/bash
rm -r dist/
uv build
UV_PUBLISH_URL=https://europe-north1-python.pkg.dev/prs-next/ponty UV_PUBLISH_USERNAME=oauth2accesstoken UV_PUBLISH_PASSWORD=$( gcloud auth application-default print-access-token ) uv publish