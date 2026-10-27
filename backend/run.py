import uvicorn

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 mAlntenance & Assistance API avec Ollama")
    print("="*60)
    print("📌 Backend: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🤖 Modèle Ollama: mistral:7b-instruct")
    print("="*60)
    print("\n💡 Assurez-vous qu'Ollama tourne: ollama serve")
    print("💡 Appuyez sur Ctrl+C pour arrêter\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )