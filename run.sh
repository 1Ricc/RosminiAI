#!/bin/bash
set -e

echo "🗺️  Ask Rovereto — avvio..."

# Verifica dati processati
if [ ! -d "data/processed" ] || [ -z "$(ls data/processed/*.geojson 2>/dev/null)" ]; then
  echo "⚠️  Dati non trovati. Eseguo riproiezione..."
  pip install pyproj -q
  python scripts/reproject.py
fi

# Backend
echo "→ Backend FastAPI su http://localhost:8000"
cd backend
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

sleep 2
curl -s http://localhost:8000/health > /dev/null && echo "  Backend OK" || echo "  Backend non risponde"

# Frontend
echo "→ Frontend Vue su http://localhost:5173"
cd frontend
npm install -q
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ App avviata:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo ""
echo "Premi Ctrl+C per fermare."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Fermato.'" EXIT
wait
