# projects

<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->

## Directory structure

<details>
<summary>Show directory tree diagram for `projects`</summary>

```mermaid
graph TD
	root["projects"]:::root --> n1("openssl-output-generator"):::folder
	root["projects"]:::root --> n2("kvm-provisioning"):::folder
	root["projects"]:::root --> n3("stftp"):::folder
	root["projects"]:::root --> n4("Wedge-400-Switch-API"):::folder
	root["projects"]:::root --> n5("terminus"):::folder
	root["projects"]:::root --> n6("antigravity-export-html5"):::folder
	root["projects"]:::root --> n7("BMC-API-Crawler"):::folder
	root["projects"]:::root --> n8["README.md"]:::file-md
	root["projects"]:::root --> n9["deploy-mailserver-debian.md"]:::file-md
	root["projects"]:::root --> n10["deploy-mailserver-debian.sh"]:::file-sh
	n1 --> n1_1["README.md"]:::file-md
	n3 --> n3_1("data"):::folder
	n2 --> n2_2["README.md<br>provision_vms.sh"]:::file-bundle
	n4 --> n4_1("tests"):::folder
	n3 --> n3_8["client.py<br>README.md<br>test.txt<br>server2.py<br>server.py<br>client2.py<br>.gitignore"]:::file-bundle
	n4 --> n4_3("src"):::folder
	n5 --> n5_1("build-from-scratch"):::folder
	n4 --> n4_11[".pytest_cache<br>context_bootstrap.md<br>build.sh<br>README.md<br>implementation_plan.md<br>deploy.sh<br>walkthrough.md<br>... +2 more"]:::file-bundle
	n6 --> n6_1("dist"):::folder
	n5 --> n5_6["DEPLOYMENT.md<br>build.sh<br>README.md<br>terminus.py<br>deploy.sh"]:::file-bundle
	n7 --> n7_1("tests"):::folder
	n6 --> n6_4["README.md<br>export.py<br>index.html"]:::file-bundle
	n7 --> n7_3("src"):::folder
	n7 --> n7_8[".pytest_cache<br>context_bootstrap.md<br>build.sh<br>README.md<br>deploy.sh<br>pyproject.toml"]:::file-bundle
	n3_1 --> n3_1_1("stftpupload"):::folder
	n3_1 --> n3_1_2["README.md"]:::file-md
	n4_2 --> n4_2_1("v"):::folder
	n4_1 --> n4_1_3["README.md<br>test_api.py<br>test_auth.py"]:::file-bundle
	n4_2 --> n4_2_4["README.md<br>CACHEDIR.TAG<br>.gitignore"]:::file-bundle
	n4_3 --> n4_3_2("fastapi_starter"):::folder
	n5_1 --> n5_1_1("images"):::folder
	n4_3 --> n4_3_3["wedge_400_switch_api.egg-info<br>README.md"]:::file-bundle
	n6_1 --> n6_1_1("markdown"):::folder
	n5_1 --> n5_1_8["dev_workflow_guide.mp3<br>README.md<br>implementation_plan.md<br>generate_voiceover.py<br>dev_workflow_guide.md<br>walkthrough.md<br>master_prompt.md"]:::file-bundle
	n6_1 --> n6_1_3["README.md<br>index.html"]:::file-bundle
	n4_2 --> n4_2_1("v"):::folder
	n4_1 --> n4_1_2["test_crawler.py"]:::file-py
	n4_3 --> n4_3_1("crawler"):::folder
	n4_2 --> n4_2_4["CACHEDIR.TAG<br>.gitignore"]:::file-bundle
	n4_3 --> n4_3_2["bmc_api_crawler.egg-info"]:::file-other
	n4_2_1 --> n4_2_1_1("cache"):::folder
	n3_1_1 --> n3_1_1_2["README.md<br>test.txt"]:::file-bundle
	n4_2_1 --> n4_2_1_2["README.md"]:::file-md
	n4_3_1 --> n4_3_1_4("PKG-INFO"):::folder
	n4_3_2 --> n4_3_2_1("templates"):::folder
	n4_3_1 --> n4_3_1_6["dependency_links.txt<br>README.md<br>requires.txt<br>SOURCES.txt<br>top_level.txt"]:::file-bundle
	n4_3_2 --> n4_3_2_8["README.md<br>auth.py<br>main.py<br>api.py<br>__init__.py<br>models.py<br>database.py"]:::file-bundle
	n6_1_1 --> n6_1_1_1("skills"):::folder
	n5_1_1 --> n5_1_1_3["README.md<br>terminus_tui_mockup.jpg<br>terminus_web_mockup.jpg"]:::file-bundle
	n4_2_1 --> n4_2_1_1("cache"):::folder
	n4_3_1 --> n4_3_1_1("templates"):::folder
	n6_1_1 --> n6_1_1_7["README.md<br>general_settings.md<br>global_skills.md<br>mcp_servers.md<br>workspace_rules.md<br>workspace_skills.md"]:::file-md
	n4_3_1 --> n4_3_1_4["main.py<br>__init__.py"]:::file-py
	n4_3_2 --> n4_3_2_4("PKG-INFO"):::folder
	n4_3_2 --> n4_3_2_6["dependency_links.txt<br>requires.txt<br>SOURCES.txt<br>top_level.txt"]:::file-text
	n4_2_1_1 --> n4_2_1_1_2("nodeids"):::folder
	n4_2_1_1 --> n4_2_1_1_3("lastfailed"):::folder
	n4_2_1_1 --> n4_2_1_1_1["README.md"]:::file-md
	n4_3_2_1 --> n4_3_2_1_2["README.md<br>index.html"]:::file-bundle
	n6_1_1_1 --> n6_1_1_1_37["workspace_wordpress-taxonomy.md<br>global_building-data-apps.md<br>global_accidental-data-loss-prevention.md<br>README.md<br>global_gcloud-auth-verification.md<br>global_gcp-composer-troubleshooting.md<br>global_gcp-pipeline-resource-provisioning.md<br>... +30 more"]:::file-md
	n4_2_1_1 --> n4_2_1_1_2("nodeids"):::folder
	n4_2_1_1 --> n4_2_1_1_3("lastfailed"):::folder
	n4_2_1_1 --> n4_2_1_1_1["README.md"]:::file-md
	n4_3_2_1 --> n4_3_2_1_2["index.html"]:::file-html
classDef root fill:#2563eb,stroke:#1e40af,stroke-width:2px,color:#ffffff;
classDef folder fill:#fbbf24,stroke:#d97706,stroke-width:1px,color:#451a03;
classDef file-bundle fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#334155;
classDef file-html fill:#ffedd5,stroke:#ea580c,stroke-width:1px,color:#7c2d12;
classDef file-md fill:#dbeafe,stroke:#3b82f6,stroke-width:1px,color:#1e3a8a;
classDef file-other fill:#f2f2f2,stroke:#9ca3af,stroke-width:1px,color:#374151;
classDef file-py fill:#dcfce7,stroke:#16a34a,stroke-width:1px,color:#14532d;
classDef file-sh fill:#ccfbf1,stroke:#0d9488,stroke-width:1px,color:#134e4a;
classDef file-text fill:#fafafa,stroke:#a3a3a3,stroke-width:1px,color:#404040;
```

</details>

<!-- AUTO-GENERATED MERMAID END -->

Auto-generated directory structure for this folder.
