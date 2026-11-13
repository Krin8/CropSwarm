# Deploy CropSwarm

The public URL is pending an authenticated hosting account. The local Streamlit app passed the three-farm browser check. The Dockerfile uses port 7860. A Docker runtime was unavailable locally, so the container build remains unverified. [Hugging Face Docker Spaces documentation](https://huggingface.co/docs/hub/spaces-sdks-docker)

1. Sign in and create a public Docker Space for CropSwarm. Upload this project's committed files. Keep `app/main.py`, `src/`, `data/processed/`, `.streamlit/`, `requirements.txt`, `README.md` and `Dockerfile` in the deployed tree.
2. Wait for the build and open the public URL in a signed-out browser.
3. Select Kansas, Telangana and Makueni. Each should show five rotations. Check Telangana's baseline violation, Makueni's cropland flag and the warmer and drier scenario before submitting the URL.

For Streamlit Community Cloud, publish the separate CropSwarm repository to an authorized GitHub destination and deploy `app/main.py`. [Streamlit Community Cloud documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)
