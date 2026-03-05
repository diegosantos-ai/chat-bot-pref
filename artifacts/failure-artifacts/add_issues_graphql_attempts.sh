#!/usr/bin/env bash
# Attempts to run the GraphQL mutation for each failed issue.
# Requires PROJECT_TOKEN env var with appropriate scopes.
echo "Attempting issue #0 (https://github.com/diegosantos-ai/pilot-atendimento/issues/5)"
echo "Provide PROJECT_TOKEN in environment before running."
curl -s -X POST -H "Authorization: bearer $PROJECT_TOKEN" -H "Content-Type: application/json" \
+  -d "{"query": "mutation { addProjectV2ItemByContentId(input: {projectId: \"PVT_kwHODI7RY84BM1k1\", contentId: \"<CONTENT_ID_HERE>\"}) { item { id } } }" }" \
+  https://api.github.com/graphql

echo "Attempting issue #1 (https://github.com/diegosantos-ai/pilot-atendimento/issues/22)"
echo "Provide PROJECT_TOKEN in environment before running."
curl -s -X POST -H "Authorization: bearer $PROJECT_TOKEN" -H "Content-Type: application/json" \
+  -d "{"query": "mutation { addProjectV2ItemByContentId(input: {projectId: \"PVT_kwHODI7RY84BM1k1\", contentId: \"<CONTENT_ID_HERE>\"}) { item { id } } }" }" \
+  https://api.github.com/graphql

echo "Attempting issue #2 (https://github.com/diegosantos-ai/pilot-atendimento/issues/21)"
echo "Provide PROJECT_TOKEN in environment before running."
curl -s -X POST -H "Authorization: bearer $PROJECT_TOKEN" -H "Content-Type: application/json" \
+  -d "{"query": "mutation { addProjectV2ItemByContentId(input: {projectId: \"PVT_kwHODI7RY84BM1k1\", contentId: \"<CONTENT_ID_HERE>\"}) { item { id } } }" }" \
+  https://api.github.com/graphql

echo "Attempting issue #3 (https://github.com/diegosantos-ai/pilot-atendimento/issues/20)"
echo "Provide PROJECT_TOKEN in environment before running."
curl -s -X POST -H "Authorization: bearer $PROJECT_TOKEN" -H "Content-Type: application/json" \
+  -d "{"query": "mutation { addProjectV2ItemByContentId(input: {projectId: \"PVT_kwHODI7RY84BM1k1\", contentId: \"<CONTENT_ID_HERE>\"}) { item { id } } }" }" \
+  https://api.github.com/graphql

echo "Attempting issue #4 (https://github.com/diegosantos-ai/pilot-atendimento/issues/19)"
echo "Provide PROJECT_TOKEN in environment before running."
curl -s -X POST -H "Authorization: bearer $PROJECT_TOKEN" -H "Content-Type: application/json" \
+  -d "{"query": "mutation { addProjectV2ItemByContentId(input: {projectId: \"PVT_kwHODI7RY84BM1k1\", contentId: \"<CONTENT_ID_HERE>\"}) { item { id } } }" }" \
+  https://api.github.com/graphql

echo "Attempting issue #5 (https://github.com/diegosantos-ai/pilot-atendimento/issues/18)"
echo "Provide PROJECT_TOKEN in environment before running."
curl -s -X POST -H "Authorization: bearer $PROJECT_TOKEN" -H "Content-Type: application/json" \
+  -d "{"query": "mutation { addProjectV2ItemByContentId(input: {projectId: \"PVT_kwHODI7RY84BM1k1\", contentId: \"<CONTENT_ID_HERE>\"}) { item { id } } }" }" \
+  https://api.github.com/graphql

echo "Attempting issue #6 (https://github.com/diegosantos-ai/pilot-atendimento/issues/17)"
echo "Provide PROJECT_TOKEN in environment before running."
curl -s -X POST -H "Authorization: bearer $PROJECT_TOKEN" -H "Content-Type: application/json" \
+  -d "{"query": "mutation { addProjectV2ItemByContentId(input: {projectId: \"PVT_kwHODI7RY84BM1k1\", contentId: \"<CONTENT_ID_HERE>\"}) { item { id } } }" }" \
+  https://api.github.com/graphql

echo "Attempting issue #7 (https://github.com/diegosantos-ai/pilot-atendimento/issues/16)"
echo "Provide PROJECT_TOKEN in environment before running."
curl -s -X POST -H "Authorization: bearer $PROJECT_TOKEN" -H "Content-Type: application/json" \
+  -d "{"query": "mutation { addProjectV2ItemByContentId(input: {projectId: \"PVT_kwHODI7RY84BM1k1\", contentId: \"<CONTENT_ID_HERE>\"}) { item { id } } }" }" \
+  https://api.github.com/graphql

echo "Attempting issue #8 (https://github.com/diegosantos-ai/pilot-atendimento/issues/15)"
echo "Provide PROJECT_TOKEN in environment before running."
curl -s -X POST -H "Authorization: bearer $PROJECT_TOKEN" -H "Content-Type: application/json" \
+  -d "{"query": "mutation { addProjectV2ItemByContentId(input: {projectId: \"PVT_kwHODI7RY84BM1k1\", contentId: \"<CONTENT_ID_HERE>\"}) { item { id } } }" }" \
+  https://api.github.com/graphql

echo "Attempting issue #9 (https://github.com/diegosantos-ai/pilot-atendimento/issues/14)"
echo "Provide PROJECT_TOKEN in environment before running."
curl -s -X POST -H "Authorization: bearer $PROJECT_TOKEN" -H "Content-Type: application/json" \
+  -d "{"query": "mutation { addProjectV2ItemByContentId(input: {projectId: \"PVT_kwHODI7RY84BM1k1\", contentId: \"<CONTENT_ID_HERE>\"}) { item { id } } }" }" \
+  https://api.github.com/graphql

