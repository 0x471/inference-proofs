#!/usr/bin/env bash
# Trial: FlashProve's Lean verifier `verify` (tools/lean-verify/lean_verify.sh, upstream at the pin,
# unpatched) on the 5 stored Level 1 proofs, then one early reject (another commitment ID).
# Runs on an HF Jobs cpu-performance host, ubuntu:24.04 by digest, the runs bucket mounted at
# /upload. Steps follow tools/lean-verify/README.md "What to type" and lean/CHECKING.md "The
# commands" 1 to 3. Each call's record is written to the bucket as soon as the call ends.
set -uo pipefail
PIN=9e2bdd8ff5bf9c62f18263d7dac189b0400b260c
HERE=${TRIAL_DIR:?}              # the trial's folder in the mounted bucket
OUT=$HERE/out; mkdir -p "$OUT"
W=/work; mkdir -p "$W/tmp"
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$OUT/job.log"; }
step() {  # NAME CMD...: run, log exit code and seconds into steps.tsv; never stop the job
  local name=$1; shift; local t0; t0=$(date +%s)
  log "step $name: start"
  "$@" > "$OUT/$name.log" 2>&1; local code=$?
  printf '%s\t%s\t%s\n' "$name" "$code" "$(( $(date +%s) - t0 ))" >> "$OUT/steps.tsv"
  log "step $name: exit $code in $(( $(date +%s) - t0 )) s; last: $(tail -n 1 "$OUT/$name.log")"
  return $code
}

log "machine: $(nproc) CPUs, $(awk '/MemTotal/{print $2" kB"}' /proc/meminfo), $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs)"
step apt bash -c 'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends git curl ca-certificates python3 g++ make diffutils time util-linux procps' || exit 1
log "g++: $(g++ --version | head -1); python3: $(python3 --version)"

step clone bash -c "git init -q $W/fp && cd $W/fp && git remote add origin https://github.com/anthropics/FlashProve.git && git fetch -q --depth 1 origin $PIN && git checkout -q FETCH_HEAD && test \"\$(git rev-parse HEAD)\" = $PIN && git rev-parse HEAD" || exit 1
cd "$W/fp/lean" || exit 1
step tree python3 -B scripts/check.py --only tree || exit 1
step elan bash -c 'curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y --default-toolchain none' || exit 1
export PATH=$HOME/.elan/bin:$PATH
step lake_version lake --version || exit 1
step cache_get lake exe cache get || exit 1
if ! ls .lake/packages/mathlib/.lake/build/ir/Mathlib/Logic/Basic.c > /dev/null 2>&1; then
  log "the fetched packages lack their .c files (README 'If a .c file is missing'): stop"; exit 1
fi
step build env LEAN_ABORT_ON_PANIC=1 /usr/bin/time -v lake build Johnson.PVR.ProgramGuard || exit 1
cd "$W/fp" || exit 1

call() {  # NAME DIR ID_FILE: one lean_verify.sh call; its record into out/calls/NAME/
  local name=$1 d=$2 id=$3 o=$OUT/calls/$1; mkdir -p "$o"
  local t0; t0=$(date +%s.%N)
  log "call $name: start"
  TMPDIR=$W/tmp /usr/bin/time -v -o "$o/time.txt" tools/lean-verify/lean_verify.sh \
    "$d/config" "$d/ivk" "$d/request.req" "$d/token.y" "$d/response.proof" "$id" \
    > "$o/stdout" 2> "$o/stderr"
  local code=$?
  local s; s=$(python3 -c "import time; print(round(time.time() - $t0, 1))")
  printf '%s\t%s\t%s\t%s\n' "$name" "$code" "$s" "$(cat "$o/stdout")" >> "$OUT/calls.tsv"
  log "call $name: exit $code in $s s: $(cat "$o/stdout")"
  rm -rf "$W"/tmp/*  # the call's ~300 MB work directory
  sync
}
for k in s2 s3 c1 c2 c3; do
  mkdir -p "$W/in/$k" && cp -r "$HERE/in/$k/." "$W/in/$k/"
  call "$k" "$W/in/$k" "$W/in/$k/ID.txt"
done
printf '%064d\n' 0 > "$W/other-id.txt"
call s2-other-id "$W/in/s2" "$W/other-id.txt"
log "done"
sync; sleep 60  # let the bucket mount flush (docs/runbooks/hf-jobs.md)
