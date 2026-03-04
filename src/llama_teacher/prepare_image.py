#!/usr/bin/env python3
"""
Script pour préparer votre image pour la vidéo
"""
import sys
from pathlib import Path

from PIL import Image


def prepare_image(input_path: str, output_path: str = None):
    """
    Prépare une image pour MoviePy
    - Convertit RGBA en RGB
    - Redimensionne
    - Optimise
    """
    if not output_path:
        output_path = input_path.replace(".png", "_prepared.jpg")

    try:
        # Ouvrir l'image
        img = Image.open(input_path)
        print(f"📷 Image originale: {img.size}, mode: {img.mode}")

        # Convertir RGBA en RGB si nécessaire
        if img.mode == "RGBA":
            print("🔄 Conversion RGBA -> RGB...")
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            if len(img.split()) == 4:
                rgb_img.paste(img, mask=img.split()[3])
            else:
                rgb_img.paste(img)
            img = rgb_img
        elif img.mode != "RGB":
            print(f"🔄 Conversion {img.mode} -> RGB...")
            img = img.convert("RGB")

        # Redimensionner si trop grand (max 1920x1080)
        max_size = (1920, 1080)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            print(f"📐 Redimensionnement...")
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Sauvegarder en JPEG
        print(f"💾 Sauvegarde: {output_path}")
        img.save(output_path, "JPEG", quality=90, optimize=True)

        print(f"✅ Image préparée: {img.size}, mode: {img.mode}")
        return True

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python prepare_image.py <chemin_image> [chemin_sortie]")
        print(
            "Exemple: python prepare_image.py assets/teacher.png assets/teacher_prepared.jpg"
        )
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(input_path).exists():
        print(f"❌ Fichier non trouvé: {input_path}")
        sys.exit(1)

    success = prepare_image(input_path, output_path)
    if success:
        print("\n🎉 Image prête pour MoviePy !")
        print(f"Utilisez ce chemin dans votre config: {output_path or input_path}")
    else:
        sys.exit(1)
