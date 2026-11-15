#!/usr/bin/env bash
# One proof build of a publisher's machine-checked theorem (RFC-0018 MC-4, MC-5), on a CPU host
# of Hugging Face Jobs (docs/runbooks/proof-build.md). Today: FlashProve's sound_of_verify_at, with
# the publisher's own command (lean/THEOREM.md L445-L457 at the pin), unpatched. The job writes
# what ran and what it printed into OUT, as it goes; `iproofs proof-build record` turns OUT into
# results/<release>/proof-build/<system>/proof-build.json. Nothing here decides a state.
#
# Environment: OUT (a folder in the mounted bucket), IMAGE (the digest the job was started from),
# BUILD_TIMEOUT_S (the build's own limit, below the job's --timeout, default 25200 = 7 h).
set -uo pipefail
REPO=anthropics/FlashProve
PIN=9e2bdd8ff5bf9c62f18263d7dac189b0400b260c
TARGET=Johnson.Goal.Skeleton.SoundOfVerifyAt
# Lean 4.29.1, which lean/lean-toolchain pins at the pin; the release archive and its sha256 as
# GitHub's release page lists them (leanprover/lean4, tag v4.29.1, asset digest).
LEAN_URL=https://github.com/leanprover/lean4/releases/download/v4.29.1/lean-4.29.1-linux.tar.zst
LEAN_SHA256=bf062d29556d655685fb287563c249ad6a8fde34352c18b5e32568a595c1aec1
: "${OUT:?}" "${IMAGE:?}"
BUILD_TIMEOUT_S=${BUILD_TIMEOUT_S:-25200}
mkdir -p "$OUT"
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$OUT/job.log"; }
meta() { printf '%s\n' "$1" >> "$OUT/meta.jsonl"; }  # one JSON object per line
stop_setup() {  # a step before the build failed: the build never started (status stopped)
  log "setup failed: $1"
  meta "{\"stopped\": \"setup\", \"step\": \"$1\"}"
  exit 1
}

if [ "$(id -u)" = 0 ]; then  # once, as root: packages and an ordinary user (lean/CHECKING.md)
  sha256sum "$0" > "$OUT/script-sha256.txt"
  log "machine: $(nproc) CPUs, $(awk '/MemTotal/{print $2" kB"}' /proc/meminfo)"
  apt-get update > "$OUT/apt.log" 2>&1 &&
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      git curl ca-certificates python3 zstd >> "$OUT/apt.log" 2>&1 || stop_setup apt
  dpkg-query -W git curl ca-certificates python3 zstd > "$OUT/packages.txt" 2>&1
  useradd -m builder || stop_setup useradd
  local_out=/home/builder/out
  mkdir -p "$local_out" && cp "$OUT"/* "$local_out"/ && chown -R builder "$local_out"
  cp "$0" /home/builder/proof-build.sh && chmod 755 /home/builder/proof-build.sh
  # The user writes below its home; root copies that folder into the bucket as it goes and at
  # the end (the mount need not be writable by the user's uid).
  ( while sleep 120; do cp -r "$local_out"/. "$OUT"/; done ) &
  copier=$!
  runuser -u builder -- env OUT="$local_out" IMAGE="$IMAGE" BUILD_TIMEOUT_S="$BUILD_TIMEOUT_S" \
    HOME=/home/builder bash /home/builder/proof-build.sh
  echo "$?" > "$local_out/runner-exit.txt"
  kill "$copier" 2> /dev/null
  cp -r "$local_out"/. "$OUT"/
  sync; sleep 60  # the bucket mount's flush (docs/runbooks/hf-jobs.md)
  exit 0
fi

cd "$HOME" || exit 1
log "user $(id -un), image $IMAGE"
curl -fsSL -o lean.tar.zst "$LEAN_URL" || stop_setup lean-download
echo "$LEAN_SHA256  lean.tar.zst" | sha256sum -c - > "$OUT/lean-sha256.txt" 2>&1 ||
  stop_setup lean-sha256
tar --zstd -xf lean.tar.zst && rm lean.tar.zst || stop_setup lean-extract
export PATH=$HOME/lean-4.29.1-linux/bin:$PATH
lean --version > "$OUT/lean-version.txt" 2>&1 && lake --version >> "$OUT/lean-version.txt" 2>&1 ||
  stop_setup lean-version
grep -q 'version 4.29.1' "$OUT/lean-version.txt" || stop_setup lean-version
log "$(tr '\n' ' ' < "$OUT/lean-version.txt")"

git init -q fp && cd fp && git remote add origin "https://github.com/$REPO.git" &&
  git fetch -q --depth 1 origin "$PIN" && git checkout -q FETCH_HEAD || stop_setup clone
[ "$(git rev-parse HEAD)" = "$PIN" ] || stop_setup clone-head
cd lean || stop_setup clone
python3 -B scripts/check.py --only tree > "$OUT/check-tree.log" 2>&1 || stop_setup check-tree
log "check.py --only tree: $(tail -n 1 "$OUT/check-tree.log")"
TOOLCHAIN=$(cat lean-toolchain)
lake exe cache get > "$OUT/cache-get.log" 2>&1 || stop_setup cache-get
if grep -q -E 'No cache files to decompress|Decompressed 0 file' "$OUT/cache-get.log"; then
  stop_setup cache-get-empty  # CHECKING.md step 3: an empty fetch would rebuild Mathlib
fi
log "cache get: $(tail -n 1 "$OUT/cache-get.log")"

# The publisher's command (THEOREM.md L452-L454), under a time limit of our own so that a stop
# is recorded with its cause before the job's own timeout.
started=$(date -u +%FT%TZ); t0=$(date +%s)
meta "{\"started_at\": \"$started\", \"image\": \"$IMAGE\", \"repo\": \"$REPO\", \"commit\": \"$(git -C .. rev-parse HEAD)\", \"toolchain_file\": \"$TOOLCHAIN\", \"target\": \"$TARGET\", \"timeout_s\": $BUILD_TIMEOUT_S}"
log "build $TARGET: start"
( while sleep 300; do cp .lake/sound_of_verify_at.log "$OUT/build.log" 2> /dev/null; done ) &
copier=$!
LEAN_ABORT_ON_PANIC=1 timeout -k 60 "$BUILD_TIMEOUT_S" lake build "$TARGET" \
  > .lake/sound_of_verify_at.log 2>&1
code=$?
seconds=$(( $(date +%s) - t0 ))
kill "$copier" 2> /dev/null
cp .lake/sound_of_verify_at.log "$OUT/build.log"
grep -A1 "sound_of_verify_at' depends" .lake/sound_of_verify_at.log > "$OUT/axioms.txt" 2>&1
meta "{\"exit_code\": $code, \"seconds\": $seconds}"
log "build $TARGET: exit status $code in $seconds s; axioms: $(tr '\n' ' ' < "$OUT/axioms.txt")"
log "done"
