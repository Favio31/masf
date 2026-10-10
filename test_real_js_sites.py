from core.fetcher import fetch_source

sitios_reales = [
    "https://github.com/Favio31/masf",
    "https://devinci.com",
    "https://3t.bike"
]

print("=" * 70)
print("🚀 PRUEBA DE PLAYWRIGHT CON SITIOS REALES DE LA ALLOWLIST")
print("=" * 70)

for url in sitios_reales:
    print(f"\n🔍 Analizando: {url}")
    print("-" * 70)
    
    result = fetch_source(url)
    
    if "error" in result:
        print(f"❌ Error: {result['error'][:100]}")
    else:
        metodo = result.get("method", "desconocido").upper()
        longitud = len(result["content"])
        
        print(f"✅ Método utilizado: {metodo}")
        print(f"✅ Longitud del contenido: {longitud} caracteres")
        
        if metodo == "PLAYWRIGHT":
            print("🎉 ¡PLAYWRIGHT SE ACTIVÓ! El sitio requiere renderizado JS.")
        else:
            print("⚡ Requests fue suficiente (el sitio sirvió HTML estático rápido).")
            
        # Mostrar un pequeño preview
        preview = result["content"][:200].replace("\n", " ")
        print(f"📄 Preview: {preview}...")

print("\n" + "=" * 70)
print("✅ Prueba completada")
print("=" * 70)
