# Domain Definitions

The user MUST define which domains to filter, and what each domain means. Fields must be unambiguous — especially "定位". Always echo the derived keyword rules back to the user for confirmation before running.

## Domain definition schema (`assets/domains.default.json`)

- `categories`: map of category id -> display label (e.g. `{"定位":"定位"}`).
- `session_rules`: ordered list of `{cat, patterns, exclude?, include?}` matched against the **session title** (lowercased, `re.search`). First match wins.
- `title_rules`: ordered list of `{cat, patterns, exclude?, include?}` matched against the **paper title**. Used when no session rule matched (supplement), or always for DBLP (no sessions).
- `fusion_split`: special-case rule for "Sensor Fusion" sessions — a paper goes to `loc_patterns` if its title contains any of them, else `default`.
- `patterns` are regex fragments. `exclude`/`include` are plain substrings (any-of).

Rule semantics: match if `patterns` any-hit, `exclude` none-hit, `include` all-hit (include is "any-of" too).

## The default domains (robotics: 感知 / 定位 / 规控)

### 规控 (planning & control)
Motion/path/task planning, trajectory generation & optimization, MPC, control (motion/force/impedance/adaptive/robust), collision avoidance, control barrier functions, stabilization, feedback controllers.

### 定位 (localization) — MUST be explicit
The robot/vehicle's **ego pose** in the world: SLAM, LiDAR/visual/inertial odometry, mapping & map construction, place recognition / relocalization, loop closure, state estimation, GNSS/IMU, extrinsic/sensor calibration, registration, navigation.

**NOT 定位**: object-level localization such as "tomato truss localization", "needle positioning", "object pose estimation for grasping", "keypoint detection". Those are 感知 (or manipulation). When a title says "localization" but refers to an object rather than the robot's own pose, put it in 感知 and note it.

### 感知 (perception)
Detection / segmentation / recognition / classification / tracking (object, human, pedestrian), depth estimation & completion, scene understanding, point-cloud processing, visual perception, RGB-D, tactile sensing, range sensing, semantic scene understanding.

## Borderline sessions (default decisions — echo & confirm with user)

| Session | Decision |
|---|---|
| `Sensor Fusion` (no SLAM) | split by title: odometry/SLAM/calibration/pose/state-estimation → 定位, else → 感知 |
| `Sensor Fusion & SLAM` | 定位 |
| `Mapping` | 定位 |
| `Navigation` / `Vision-Based Navigation` / `Autonomous Vehicle Navigation` | 定位 (not `Telerobotics and Navigation`) |
| `SLAM and Control` | 定位 |
| `VR and Vision-Based Planning` / `Vision-Based Planning` | 规控 |
| `Semantic Scene Understanding: Segmentation and Mapping` | 感知 |
| `Intention Recognition` | 感知 |
| `Aerial Systems: Mechanics and Control` / `Modeling, Control, and Learning for Soft Robots` | 规控 (contains control) |

## Customizing

1. Copy `assets/domains.default.json` to a working copy.
2. Edit `categories` (rename/add/remove domains) and the rules' `patterns`.
3. Pass `--domains <file>` to `classify_papers.py`.
4. Echo the derived rules + counts + a sample of borderline hits to the user before writing output.
