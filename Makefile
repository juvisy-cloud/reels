SHELL := /bin/bash
COMFY_DIR ?= $(HOME)/ComfyUI
ENGINES_DIR ?= $(HOME)/ai-engines
SADTALKER_DIR := $(ENGINES_DIR)/SadTalker
KOKORO_DIR := $(ENGINES_DIR)/kokoro
SADTALKER_REL := https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc
FACEXLIB_REL := https://github.com/xinntao/facexlib/releases/download/v0.1.0
KOKORO_REL := https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0

.PHONY: install install-backend install-frontend comfy-install sadtalker-install models comfy backend frontend run test lint

install: install-backend install-frontend comfy-install sadtalker-install models ## Todo, la primera vez

install-backend:
	cd backend && uv sync -p 3.12

install-frontend:
	cd frontend && npm install

comfy-install: ## ComfyUI en CPU + nodo RMBG + nodo propio de SadTalker
	test -d $(COMFY_DIR) || git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git $(COMFY_DIR)
	test -d $(COMFY_DIR)/.venv || uv venv -p 3.12 $(COMFY_DIR)/.venv
	uv pip install -p $(COMFY_DIR)/.venv/bin/python torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
	uv pip install -p $(COMFY_DIR)/.venv/bin/python -r $(COMFY_DIR)/requirements.txt
	test -d $(COMFY_DIR)/custom_nodes/ComfyUI-RMBG || git clone --depth 1 https://github.com/1038lab/ComfyUI-RMBG.git $(COMFY_DIR)/custom_nodes/ComfyUI-RMBG
	uv pip install -p $(COMFY_DIR)/.venv/bin/python -r $(COMFY_DIR)/custom_nodes/ComfyUI-RMBG/requirements.txt
	ln -sfn $(CURDIR)/comfyui_nodes/reels_studio $(COMFY_DIR)/custom_nodes/reels_studio

sadtalker-install: ## SadTalker aislado (sus dependencias antiguas romperían ComfyUI)
	test -d $(SADTALKER_DIR) || git clone --depth 1 https://github.com/OpenTalker/SadTalker.git $(SADTALKER_DIR)
	test -d $(SADTALKER_DIR)/.venv || uv venv -p 3.10 $(SADTALKER_DIR)/.venv
	uv pip install -p $(SADTALKER_DIR)/.venv/bin/python torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cpu
	uv pip install -p $(SADTALKER_DIR)/.venv/bin/python -r $(CURDIR)/comfyui_nodes/reels_studio/sadtalker-requirements.txt
	mkdir -p $(ENGINES_DIR)/bin && ln -sf "$$($(SADTALKER_DIR)/.venv/bin/python -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')" $(ENGINES_DIR)/bin/ffmpeg

models: ## Pesos de SadTalker y voz Kokoro (~1.6 GB)
	mkdir -p $(SADTALKER_DIR)/checkpoints $(SADTALKER_DIR)/gfpgan/weights $(KOKORO_DIR)
	for f in mapping_00109-model.pth.tar mapping_00229-model.pth.tar SadTalker_V0.0.2_256.safetensors; do \
	  test -f $(SADTALKER_DIR)/checkpoints/$$f || curl -fSL -o $(SADTALKER_DIR)/checkpoints/$$f $(SADTALKER_REL)/$$f; done
	for f in alignment_WFLW_4HG.pth detection_Resnet50_Final.pth; do \
	  test -f $(SADTALKER_DIR)/gfpgan/weights/$$f || curl -fSL -o $(SADTALKER_DIR)/gfpgan/weights/$$f $(FACEXLIB_REL)/$$f; done
	for f in kokoro-v1.0.onnx voices-v1.0.bin; do \
	  test -f $(KOKORO_DIR)/$$f || curl -fSL -o $(KOKORO_DIR)/$$f $(KOKORO_REL)/$$f; done

comfy: ## Arranca ComfyUI en CPU (http://127.0.0.1:8188)
	cd $(COMFY_DIR) && .venv/bin/python main.py --cpu --listen 127.0.0.1 --port 8188

backend: ## API en http://127.0.0.1:8000
	cd backend && uv run reels-studio

frontend: ## Editor en http://localhost:5173
	cd frontend && npm run dev

run: ## Arranca los tres servicios juntos (Ctrl+C detiene todo)
	trap 'kill 0' EXIT; $(MAKE) comfy & $(MAKE) backend & $(MAKE) frontend & wait

test:
	cd backend && uv run pytest -q

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy src
	cd frontend && npm run lint && npm run typecheck
	gitleaks detect --no-banner --source . || true
