from requests_html import HTMLSession
import sys

url = "https://delfi.rs/knjige/111117-ohridski-prolog-knjiga-delfi-knjizare.html"

try:
    session = HTMLSession()
    response = session.get(url)

    # Render JavaScript - this will take some time as it launches a headless browser
    print("Rendering JavaScript...", file=sys.stderr)
    response.html.render(timeout=30, sleep=3)

    # Save the rendered HTML
    with open("d:/temp/delfi_rendered.html", "w", encoding="utf-8") as f:
        f.write(response.html.html)

    print("Rendered HTML saved to d:/temp/delfi_rendered.html", file=sys.stderr)

    # Search for the categories mentioned
    categories = ["Autobiografije i biografije", "Domaći pisci", "Religija i mitologija", "Teologija"]

    for category in categories:
        elements = response.html.find(f':contains("{category}")')
        if elements:
            print(f"\n\n===== Found '{category}' in {len(elements)} elements =====", file=sys.stderr)
            for elem in elements[:3]:  # Show first 3 matches
                print(f"\nTag: {elem.tag}", file=sys.stderr)
                print(f"Classes: {elem.attrs.get('class', 'No class')}", file=sys.stderr)
                print(f"ID: {elem.attrs.get('id', 'No ID')}", file=sys.stderr)
                print(f"Text: {elem.text[:100]}...", file=sys.stderr)
                print(f"HTML: {elem.html[:200]}...", file=sys.stderr)

    session.close()
    print("\n\nDone!", file=sys.stderr)

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
