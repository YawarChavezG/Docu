# ════════════════════════════════════════════════════════════════
# Frontend — Node 22 Alpine (Vite dev server)
# ════════════════════════════════════════════════════════════════

FROM node:22-alpine

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar deps
RUN npm install

# Copiar el resto
COPY . .

EXPOSE 5173

# Vite con host 0.0.0.0 para que sea accesible desde fuera del contenedor
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
