# SPDX-License-Identifier: AGPL-3.0-only
"""Command-line entry points; GUI display and model loading are opt-in."""
import argparse
import csv
import json
from pathlib import Path
import cv2
from .core import calibrate_focal, estimate_distance, positive, read_ranging_config
from .aruco import detect_poses
from .demo import run_demo


def write_json(path, value):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def run_yolo(args):
    # Delay importing the optional model library until the command is selected.
    if not Path(args.model).is_file():
        raise ValueError("--model must point to an existing local model file")
    from ultralytics import YOLO
    focal, heights = read_ranging_config(args.config)
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    source = int(args.source) if args.source.isdecimal() else args.source
    model = YOLO(args.model)
    for frame_index, result in enumerate(model.predict(source=source, stream=True, verbose=False)):
        records = []
        image = result.orig_img.copy()
        for box in result.boxes:
            label = result.names[int(box.cls.item())]
            x1, y1, x2, y2 = [float(x) for x in box.xyxy[0].cpu().tolist()]
            # Unknown size and boxes cut off by the image border cannot provide a valid estimate.
            if label not in heights or min(x1, y1) <= 0 or x2 >= image.shape[1] - 1 or y2 >= image.shape[0] - 1:
                continue
            if y2 <= y1:
                continue
            distance = estimate_distance(focal, heights[label], y2-y1)
            records.append({"label": label, "confidence": float(box.conf.item()),
                            "bbox_xyxy_px": [x1, y1, x2, y2], "distance_m": distance})
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 180, 0), 2)
            cv2.putText(image, f"{label} ~{distance:.2f} m", (int(x1), max(20, int(y1)-8)),
                        cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 120, 0), 2)
        if not cv2.imwrite(str(out / f"frame_{frame_index:06d}.jpg"), image):
            raise ValueError("could not save output image")
        write_json(out / f"frame_{frame_index:06d}.json", records)
        if args.show:
            cv2.imshow("Size-prior ranging", image)
            if cv2.waitKey(1) & 0xff == 27:
                break
        if frame_index + 1 >= args.max_frames:
            break
    cv2.destroyAllWindows()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Monocular size-prior ranging and ArUco pose tools")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("demo", help="generate synthetic examples; no model or camera required")
    p.add_argument("--output", default="output/demo")
    p = sub.add_parser("calibrate", help="estimate focal length from one known object")
    p.add_argument("--pixel-height", type=float, required=True)
    p.add_argument("--real-height-m", type=float, required=True)
    p.add_argument("--distance-m", type=float, required=True)
    p.add_argument("--label", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("range", help="compute distance from a measured box height")
    p.add_argument("--config", required=True); p.add_argument("--label", required=True)
    p.add_argument("--pixel-height", type=float, required=True)
    p = sub.add_parser("evaluate", help="evaluate a CSV of independently measured distances")
    p.add_argument("--config", required=True); p.add_argument("--csv", required=True)
    p.add_argument("--output", default="output/evaluation.json")
    p = sub.add_parser("aruco", help="estimate marker-to-camera transforms")
    p.add_argument("--image", required=True); p.add_argument("--camera", required=True)
    p.add_argument("--marker-size-m", type=float, required=True)
    p.add_argument("--dictionary", default="DICT_4X4_50")
    p.add_argument("--output", default="output/aruco")
    p = sub.add_parser("detect", help="optional YOLO detection and size-prior ranging")
    p.add_argument("--source", required=True); p.add_argument("--model", required=True)
    p.add_argument("--config", required=True); p.add_argument("--output", default="output/detect")
    p.add_argument("--show", action="store_true"); p.add_argument("--max-frames", type=int, default=100)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            print(json.dumps(run_demo(args.output), indent=2))
        elif args.command == "calibrate":
            focal = calibrate_focal(args.pixel_height, args.real_height_m, args.distance_m)
            write_json(args.output, {"focal_px": focal,
                                    "object_heights_m": {args.label: args.real_height_m}})
            print(f"focal_px={focal:.6f}")
        elif args.command == "range":
            focal, heights = read_ranging_config(args.config)
            print(f"{estimate_distance(focal, heights[args.label], args.pixel_height):.6f} m")
        elif args.command == "evaluate":
            focal, heights = read_ranging_config(args.config)
            rows = []
            with Path(args.csv).open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    truth = positive(row["distance_m"], "distance_m")
                    value = estimate_distance(focal, heights[row["label"]], row["pixel_height"])
                    rows.append({"distance_m": truth, "estimated_distance_m": value,
                                 "absolute_error_m": abs(value-truth)})
            if not rows:
                raise ValueError("evaluation CSV must contain measurements")
            write_json(args.output, {"sample_count": len(rows), "measurements": rows,
                                    "mae_m": sum(r["absolute_error_m"] for r in rows)/len(rows)})
        elif args.command == "aruco":
            camera = json.loads(Path(args.camera).read_text(encoding="utf-8"))
            image, poses = detect_poses(cv2.imread(args.image), camera, args.marker_size_m, args.dictionary)
            out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(out / "annotated.png"), image):
                raise ValueError("could not save output image")
            write_json(out / "poses.json", {"transform": "marker_to_camera", "poses": poses})
            print(f"markers={len(poses)}")
        elif args.command == "detect":
            if args.max_frames < 1:
                raise ValueError("--max-frames must be positive")
            run_yolo(args)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
