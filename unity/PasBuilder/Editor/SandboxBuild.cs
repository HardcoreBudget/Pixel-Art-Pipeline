// Builds a .pas from a JSON job written by scenes/agentdraw/pas.py (export_job), through the plugin's own StudioScript
// front door, then re-opens the saved file and renders every frame with the plugin's DocumentCompositor, so the PNGs
// prove what the .pas really contains. Put this folder in a SCRATCH Unity project that has Pixel Art Studio installed
// (never your real project), then:
//
//   Unity -batchmode -nographics -projectPath <scratch project> -executeMethod
//       PipelineSandbox.SandboxBuild.Run -job /abs/knight.json -pas Assets/Built/Knight.pas -render /abs/out_dir -quit
//
// scenes/agentdraw/pas.py runs exactly this (UNITY_EDITOR, PAS_SANDBOX). MIT, part of Pixel-Art-Pipeline.
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using PixelArtStudio.Editor.Commands;
using PixelArtStudio.Editor.Documents;
using PixelArtStudio.Editor.Scripting;
using PixelArtStudio.Editor.Stores;

namespace PipelineSandbox
{
    [Serializable] public class JCel { public int frame; public int[] indices; }
    [Serializable] public class JLayer { public string name; public string parent; public bool group; public JCel[] cels;
        public bool hidden; public int opacity; public bool locked; }   // opacity 0 = leave at 255
    [Serializable] public class JFrame { public int duration; }
    [Serializable] public class JTag { public string name; public int from; public int to; public bool loops = true; }
    [Serializable] public class JTiles { public int tileWidth; public int tileHeight; public int mapWidth; public int mapHeight;
        public int[] cells; }   // row-major pairs: col0,row0,col1,row1,... (-1,-1 = empty)
    [Serializable] public class JPose { public string layer; public int frame; public float angle; public float x; public float y; public float pivotX; public float pivotY; }
    [Serializable]
    public class JDoc
    {
        public string name; public int width; public int height;
        public string[] palette;          // "#RRGGBB" (index 0 is transparent and not listed)
        public JLayer[] layers;           // bottom first
        public JFrame[] frames;
        public JTag[] tags;
        public JPose[] poses;
        public JTiles tiles;              // optional: tile size + the Tiles tab's scratchpad map
    }

    public static class SandboxBuild
    {
        static string Arg(string name)
        {
            var a = Environment.GetCommandLineArgs();
            for (int i = 0; i < a.Length - 1; i++) if (a[i] == name) return a[i + 1];
            return null;
        }

        public static void Run()
        {
            int code = 0;
            try
            {
                var list = Arg("-jobs");   // many documents in one Unity run: lines "job.json|Assets/Built/X.pas|/render/dir"
                if (list != null)
                    foreach (var line in File.ReadAllLines(list))
                    {
                        if (string.IsNullOrWhiteSpace(line)) continue;
                        var f = line.Split('|');
                        Build(f[0], f[1], f.Length > 2 ? f[2] : null);
                    }
                else Build(Arg("-job"), Arg("-pas"), Arg("-render"));
            }
            catch (Exception e) { Debug.LogError("[SandboxBuild] FAILED: " + e); code = 1; }
            EditorApplication.Exit(code);
        }

        static void Check(CommandResult r, string what)
        {
            if (!r.Success) throw new InvalidOperationException($"{what}: {r.Message}");
        }

        public static void Build(string jobPath, string pasPath, string renderDir)
        {
            var doc = JsonUtility.FromJson<JDoc>(File.ReadAllText(jobPath));
            Directory.CreateDirectory(Path.GetDirectoryName(pasPath));
            var blank = PixelDocument.CreateBlank(doc.width, doc.height, ColorMode.Indexed);
            new PasStore(pasPath).Save(blank);
            AssetDatabase.ImportAsset(pasPath, ImportAssetOptions.ForceSynchronousImport);
            ScriptSession s = StudioScript.Open(pasPath);

            var colors = new Color32[doc.palette.Length + 1];
            colors[0] = new Color32(0, 0, 0, 0);
            for (int i = 0; i < doc.palette.Length; i++)
            {
                ColorUtility.TryParseHtmlString(doc.palette[i], out Color c);
                colors[i + 1] = c;
            }
            int n = doc.width * doc.height;
            var index = new Dictionary<string, int>();
            for (int l = 0; l < doc.layers.Length; l++) index[doc.layers[l].name] = l;

            Check(s.Batch($"{doc.name}: structure", b =>
            {
                b.Do("pas.palette.set", ("colors", colors));
                b.Do("pas.layer.properties", ("layer", 0), ("name", doc.layers[0].name));
                for (int l = 1; l < doc.layers.Length; l++)
                    b.Do("pas.layer.add", ("name", doc.layers[l].name), ("index", l));
                for (int f = 1; f < doc.frames.Length; f++)
                    b.Do("pas.frame.add", ("index", f));
                for (int f = 0; f < doc.frames.Length; f++)
                    b.Do("pas.frame.duration", ("frame", f), ("durationMs", Math.Max(1, doc.frames[f].duration)));
            }), "structure");

            // pixels, one batch per frame (groups own no cels: they are bones)
            for (int f = 0; f < doc.frames.Length; f++)
            {
                int frame = f;
                Check(s.Batch($"{doc.name}: frame {f} pixels", b =>
                {
                    for (int l = 0; l < doc.layers.Length; l++)
                    {
                        var L = doc.layers[l];
                        if (L.group || L.cels == null) continue;
                        foreach (var cel in L.cels)
                        {
                            if (cel.frame != frame || cel.indices == null || cel.indices.Length != n) continue;
                            var cov = new bool[n]; var idx = new byte[n]; bool any = false;
                            for (int i = 0; i < n; i++) { if (cel.indices[i] > 0) { cov[i] = true; idx[i] = (byte)cel.indices[i]; any = true; } }
                            if (!any) continue;
                            b.Do("pas.pixels.paste", ("layer", l), ("frame", frame), ("x", 0), ("y", 0),
                                 ("width", doc.width), ("height", doc.height), ("coverage", cov), ("indices", idx));
                        }
                    }
                }), $"frame {f} pixels");
            }

            // bones: the plugin has no re-parent command; the hierarchy is the layer ParentIndex (set on the model)
            for (int l = 0; l < doc.layers.Length; l++)
            {
                var p = doc.layers[l].parent;
                s.Document.Layers[l].ParentIndex = string.IsNullOrEmpty(p) ? Layer.NoParent : index[p];
            }

            // reference layers (an onion-skin silhouette): faint, locked, hidden once the frames are drawn
            Check(s.Batch($"{doc.name}: layer properties", b =>
            {
                for (int l = 0; l < doc.layers.Length; l++)
                {
                    var L = doc.layers[l];
                    if (L.opacity > 0 && L.opacity < 255) b.Do("pas.layer.properties", ("layer", l), ("opacity", (byte)L.opacity));
                    if (L.hidden) b.Do("pas.layer.properties", ("layer", l), ("visible", false));
                }
            }), "layer properties");

            if (doc.poses != null && doc.poses.Length > 0)
                Check(s.Batch($"{doc.name}: poses", b =>
                {
                    foreach (var p in doc.poses)
                        b.Do("pas.pose.set", ("layer", index[p.layer]), ("frame", p.frame), ("angle", p.angle),
                             ("x", p.x), ("y", p.y), ("pivotX", p.pivotX), ("pivotY", p.pivotY));
                }), "poses");
            if (doc.tags != null && doc.tags.Length > 0)
                Check(s.Batch($"{doc.name}: tags", b =>
                {
                    foreach (var t in doc.tags)
                        b.Do("pas.tag.add", ("name", t.name), ("from", t.from), ("to", t.to), ("loops", t.loops));
                }), "tags");
            if (doc.tiles != null && doc.tiles.tileWidth > 0)
            {
                var T = doc.tiles;
                var cells = new Vector2Int[T.mapWidth * T.mapHeight];
                for (int i = 0; i < cells.Length; i++) cells[i] = new Vector2Int(T.cells[2 * i], T.cells[2 * i + 1]);
                Check(s.Batch($"{doc.name}: tiles", b =>
                    b.Do("pas.tiles.set", ("tileWidth", T.tileWidth), ("tileHeight", T.tileHeight),
                         ("mapWidth", T.mapWidth), ("mapHeight", T.mapHeight), ("cells", cells))), "tiles");
            }
            // lock last: a locked layer refuses edits, including the property changes above
            bool anyLocked = false;
            foreach (var L in doc.layers) anyLocked |= L.locked;
            if (anyLocked)
                Check(s.Batch($"{doc.name}: locks", b =>
                {
                    for (int l = 0; l < doc.layers.Length; l++)
                        if (doc.layers[l].locked) b.Do("pas.layer.properties", ("layer", l), ("locked", true));
                }), "locks");
            s.Save();
            AssetDatabase.ImportAsset(pasPath, ImportAssetOptions.ForceSynchronousImport);

            if (!string.IsNullOrEmpty(renderDir))
            {
                Directory.CreateDirectory(renderDir);
                var reread = new PasStore(pasPath).Load();   // what is really on disk
                for (int f = 0; f < reread.Frames.Count; f++)
                {
                    var px = DocumentCompositor.Composite(reread, f);   // row-major, top-down
                    var tex = new Texture2D(reread.Width, reread.Height, TextureFormat.RGBA32, false);
                    var flipped = new Color32[px.Length];
                    for (int y = 0; y < reread.Height; y++)
                        Array.Copy(px, y * reread.Width, flipped, (reread.Height - 1 - y) * reread.Width, reread.Width);
                    tex.SetPixels32(flipped); tex.Apply();
                    File.WriteAllBytes(Path.Combine(renderDir, $"pas_frame_{f:D2}.png"), tex.EncodeToPNG());
                    UnityEngine.Object.DestroyImmediate(tex);
                }
                File.WriteAllText(Path.Combine(renderDir, "inspect.txt"), StudioScript.Open(pasPath).Inspect());
            }
            Debug.Log($"[SandboxBuild] OK {pasPath}: {doc.layers.Length} layers, {doc.frames.Length} frames");
        }
    }
}
