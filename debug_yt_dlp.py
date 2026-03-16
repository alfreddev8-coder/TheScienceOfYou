import yt_dlp

def test_search(prefix, query):
    print(f"Testing {prefix} for {query}...")
    ydl_opts = {'extract_flat': True, 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(f"{prefix}:{query}", download=False)
            if 'entries' in res:
                print(f"  {prefix} works! Found {len(res['entries'])} results.")
                return True
            print(f"  {prefix} returned no entries.")
    except Exception as e:
        print(f"  {prefix} failed: {e}")
    return False

prefixes = ["kwaisearch5", "kwaisearch", "kuaishousearch", "tiktoksearch", "tiktoksearch5"]
for p in prefixes:
    test_search(p, "satisfying")
