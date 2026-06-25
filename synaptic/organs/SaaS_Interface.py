"""
Production Synapse Layer — SaaS_Interface.py

Five biological organs mapped to industry SaaS services.
All neurons must route through SynapticOrganInterface; never call provider
SDKs directly from agent code.

Organ map:
  Metabolism      → Upstash Redis    GlobalMetabolicLock
  Hippocampus     → Supabase         SupabaseMemoryProvider
  Nociceptors     → Sentry           SentryNociceptor
  Sensory Input   → PostHog          PostHogSensoryFeedback
  Efferent (out)  → Resend + Twilio  ResendSynapse / TwilioReflex

Abstraction rule: swap any provider (e.g. Stripe → local mock) without
touching a single line of agent code — only this file changes.
"""
from __future__ import annotations

import asyncio
import base64
import datetime
import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Dict, List, Optional, Union

import httpx

from synaptic.config import settings
from synaptic.utils.exceptions import ConfigurationError, ModelProviderError, WorkflowError
from synaptic.utils.logger import synaptic_log


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ORGAN 1 — METABOLISM
# Upstash Redis: GlobalMetabolicLock coordinates the 5-Account Gemini Key Pool
# across every distributed Synapticity instance, eliminating Synaptic Collisions
# (rate-limit hits caused by two workers picking the same exhausted key).
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GlobalMetabolicLock:
    """
    Distributed coordinator for the Gemini multi-key pool via Upstash Redis.

    Redis key schema
    ────────────────
    synapse:gemini:global_lock         SETNX distributed lock (30-s TTL)
    synapse:gemini:key_index           current active key index (int)
    synapse:gemini:cooldown:<index>    present iff key <index> is exhausted
    """

    _LOCK_KEY      = "synapse:gemini:global_lock"
    _INDEX_KEY     = "synapse:gemini:key_index"
    _COOLDOWN_PFX  = "synapse:gemini:cooldown:"
    _LOCK_TTL      = 30   # seconds — prevents stale locks after crashes
    _ACQUIRE_POLL  = 0.5  # seconds between lock-acquire retries
    _MAX_WAIT      = 300  # 5-minute global wait cap before hard failure

    def __init__(self) -> None:
        url   = os.getenv("UPSTASH_REDIS_URL", "")
        token = os.getenv("UPSTASH_REDIS_TOKEN", "")
        if not url or not token:
            raise ConfigurationError(
                "Upstash Redis not configured. "
                "Set UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN."
            )
        # Import lazily so missing package doesn't break unrelated organs
        from upstash_redis.asyncio import Redis
        self._redis = Redis(url=url, token=token)

    # ── distributed lock primitives ───────────────────────────────────────────

    async def _try_acquire_lock(self) -> Optional[str]:
        """SET NX EX — atomically acquires the global lock. Returns lock_value or None."""
        lock_value = str(uuid.uuid4())
        result = await self._redis.set(
            self._LOCK_KEY, lock_value, nx=True, ex=self._LOCK_TTL
        )
        return lock_value if result else None

    async def _release_lock(self, lock_value: str) -> None:
        """Atomic check-and-delete via Lua to avoid releasing a lock we no longer own."""
        lua = (
            "if redis.call('get',KEYS[1])==ARGV[1] then "
            "return redis.call('del',KEYS[1]) "
            "else return 0 end"
        )
        await self._redis.eval(lua, keys=[self._LOCK_KEY], args=[lock_value])

    # ── public API ────────────────────────────────────────────────────────────

    async def acquire_key_slot(self, num_keys: int) -> int:
        """
        Atomically selects the next available Gemini key not currently in cooldown.
        Blocks (polls) until a key is free or _MAX_WAIT is exceeded.

        Returns the zero-based key index the caller is permitted to use.
        """
        deadline = time.monotonic() + self._MAX_WAIT

        while time.monotonic() < deadline:
            lock_val = await self._try_acquire_lock()
            if not lock_val:
                await asyncio.sleep(self._ACQUIRE_POLL)
                continue

            try:
                current_raw = await self._redis.get(self._INDEX_KEY)
                current_idx = int(current_raw) if current_raw else 0

                for offset in range(num_keys):
                    candidate = (current_idx + offset) % num_keys
                    cooldown_key = f"{self._COOLDOWN_PFX}{candidate}"
                    is_exhausted = await self._redis.exists(cooldown_key)

                    if not is_exhausted:
                        # Write the NEXT index so the following caller starts past this
                        # key, preventing two instances from racing to claim the same slot.
                        next_idx = (candidate + 1) % num_keys
                        await self._redis.set(self._INDEX_KEY, str(next_idx))
                        synaptic_log.debug(
                            f"[Metabolism] Acquired key slot {candidate} (next={next_idx})"
                        )
                        return candidate

                # All keys in cooldown — release lock and back off
            finally:
                await self._release_lock(lock_val)

            await asyncio.sleep(10)

        raise ModelProviderError(
            "GlobalMetabolicLock: all Gemini keys exhausted globally "
            f"(waited {self._MAX_WAIT}s). Check GEMINI_KEY_* env vars."
        )

    async def mark_key_exhausted(
        self, key_index: int, cooldown_seconds: float = 60.0
    ) -> None:
        """
        Broadcasts a key's exhaustion across all distributed instances.
        Stored with a TTL equal to the cooldown so Redis auto-expires it.
        """
        cooldown_key = f"{self._COOLDOWN_PFX}{key_index}"
        await self._redis.set(
            cooldown_key,
            str(time.time() + cooldown_seconds),
            ex=int(cooldown_seconds) + 5,  # slight buffer for clock drift
        )
        synaptic_log.warning(
            f"[Metabolism] Key {key_index} marked exhausted globally for {cooldown_seconds}s"
        )

    async def release_key_slot(self, key_index: int) -> None:
        """Clears the cooldown for a key early (e.g. after a successful call)."""
        await self._redis.delete(f"{self._COOLDOWN_PFX}{key_index}")

    async def health_check(self) -> dict:
        try:
            await self._redis.ping()
            return {"organ": "metabolism", "status": "healthy"}
        except Exception as exc:
            return {"organ": "metabolism", "status": "degraded", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ORGAN 2 — HIPPOCAMPUS  (Long-Term Potentiation)
# Supabase Postgres + pgvector: agents accumulate experience permanently.
# Successful fixes, architectural insights, and behavioural patterns are
# embedded and retrieved semantically so every future mission benefits from
# every past one.  Row Level Security prevents agents from reading or
# deleting data outside their own mission namespace.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SupabaseMemoryProvider:
    """
    Long-Term Potentiation: durable semantic memory for agent reflections.

    Table: neural_firings  (see migrations/001_neural_firings.sql)
    Embedding model: Gemini text-embedding-004 (768 dim)
    Similarity function: cosine distance via pgvector <=> operator
    """

    EMBEDDING_DIM    = 768  # Gemini text-embedding-004
    TABLE            = "neural_firings"
    RPC_MATCH        = "match_neural_firings"
    RPC_MATCH_TYPED  = "match_neural_firings_typed"

    def __init__(self) -> None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_ANON_KEY", "")
        if not url or not key:
            raise ConfigurationError(
                "Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY."
            )
        from supabase import create_client
        self._client = create_client(url, key)
        # Reuse first Gemini key for embeddings (read-only, cheap quota)
        self._gemini_key = settings.GEMINI_KEYS[0] if settings.GEMINI_KEYS else ""

    # ── embedding ─────────────────────────────────────────────────────────────

    async def _embed(self, text: str) -> List[float]:
        """Returns a 768-dim semantic vector using Gemini text-embedding-004."""
        if not self._gemini_key:
            synaptic_log.warning("[Hippocampus] No Gemini key — storing zero vector")
            return [0.0] * self.EMBEDDING_DIM
        try:
            from google import genai
            client = genai.Client(api_key=self._gemini_key)
            response = await asyncio.to_thread(
                client.models.embed_content,
                model="text-embedding-004",
                content=text,
            )
            return list(response.embeddings[0].values)
        except Exception as exc:
            synaptic_log.warning(f"[Hippocampus] Embedding failed: {exc}")
            return [0.0] * self.EMBEDDING_DIM

    # ── writes ────────────────────────────────────────────────────────────────

    async def store_reflection(
        self,
        mission_id: str,
        agent_name: str,
        reflection_type: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Potentiates a neural firing into long-term memory.

        reflection_type is an open enum: 'fix', 'insight', 'pattern', 'audit',
        'architecture', 'security_finding' — choose the closest label.

        Returns the UUID of the created row.
        """
        embedding = await self._embed(content)
        payload = {
            "mission_id":      mission_id,
            "agent_name":      agent_name,
            "reflection_type": reflection_type,
            "content":         content,
            "embedding":       embedding,
            "metadata":        metadata or {},
        }
        result = await asyncio.to_thread(
            lambda: self._client.table(self.TABLE).insert(payload).execute()
        )
        if not result.data:
            raise WorkflowError(f"[Hippocampus] Supabase insert returned no data: {result}")

        row_id = result.data[0]["id"]
        synaptic_log.info(
            f"[Hippocampus] Reflection stored: {reflection_type} / {agent_name} → {row_id}"
        )
        return row_id

    async def store_successful_fix(
        self,
        mission_id: str,
        bug_description: str,
        fix_applied: str,
        context: str = "",
    ) -> str:
        """Persists a completed repair cycle as a learnable synaptic pattern."""
        content = (
            f"BUG: {bug_description}\n\n"
            f"FIX: {fix_applied}\n\n"
            f"CONTEXT: {context}"
        )
        return await self.store_reflection(
            mission_id=mission_id,
            agent_name="healing_cycle",
            reflection_type="fix",
            content=content,
            metadata={
                "bug_length": len(bug_description),
                "fix_length": len(fix_applied),
            },
        )

    # ── reads ─────────────────────────────────────────────────────────────────

    async def semantic_lookup(
        self,
        query: str,
        limit: int = 5,
        reflection_type: Optional[str] = None,
    ) -> List[dict]:
        """
        Semantic nearest-neighbour search over all past neural firings.
        Calls the Postgres RPC function defined in migrations/001_neural_firings.sql.

        Returns list of dicts: {id, mission_id, agent_name, reflection_type,
                                 content, similarity, metadata}.
        """
        query_vector = await self._embed(query)
        params: dict = {"query_embedding": query_vector, "match_count": limit}
        rpc = self.RPC_MATCH_TYPED if reflection_type else self.RPC_MATCH
        if reflection_type:
            params["filter_type"] = reflection_type

        result = await asyncio.to_thread(
            lambda: self._client.rpc(rpc, params).execute()
        )
        return result.data or []

    async def health_check(self) -> dict:
        try:
            await asyncio.to_thread(
                lambda: self._client.table(self.TABLE).select("id").limit(1).execute()
            )
            return {"organ": "hippocampus", "status": "healthy"}
        except Exception as exc:
            return {"organ": "hippocampus", "status": "degraded", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ORGAN 3 — NOCICEPTORS  (Pain Receptors)
# Sentry webhook → High_Priority_Reflex → autonomous heal → GitHub commit →
# Sentry auto-resolve.  If the heal loop itself fails 3× the TwilioReflex
# (biological alarm) is triggered.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SentryNociceptor:
    """
    Pain Receptor: detects production runtime errors via Sentry webhooks
    and triggers an autonomous self-healing reflex arc.

    Flow
    ────
    Sentry webhook → validate_webhook_signature()
                   → extract_pain_signal()
                   → trigger_high_priority_reflex()  (On-Call Auditor agent)
                   → dispatch_github_heal()           (GitHub REST API commit)
                   → resolve_sentry_issue()           (Sentry API)
    """

    _SENTRY_API = "https://sentry.io/api/0"

    def __init__(self) -> None:
        self._auth_token      = os.getenv("SENTRY_AUTH_TOKEN", "")
        self._webhook_secret  = os.getenv("SENTRY_WEBHOOK_SECRET", "")
        self._org_slug        = os.getenv("SENTRY_ORG_SLUG", "")
        self._http            = httpx.AsyncClient(timeout=30)

    # ── webhook validation ────────────────────────────────────────────────────

    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verifies the Sentry HMAC-SHA256 'sentry-hook-signature' header.
        Returns True if secret is unconfigured (dev mode) so startup isn't blocked.
        """
        if not self._webhook_secret:
            synaptic_log.warning(
                "[Nociceptor] SENTRY_WEBHOOK_SECRET not set — skipping signature check"
            )
            return True
        expected = hmac.new(
            self._webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        received = signature.lstrip("sha256=")
        return hmac.compare_digest(expected, received)

    # ── signal extraction ─────────────────────────────────────────────────────

    def extract_pain_signal(self, sentry_event: dict) -> dict:
        """Parses a Sentry 'issue' webhook payload into a structured pain signal."""
        issue = sentry_event.get("data", {}).get("issue", {})
        return {
            "issue_id":   issue.get("id", ""),
            "title":      issue.get("title", "Unknown Error"),
            "culprit":    issue.get("culprit", ""),
            "level":      issue.get("level", "error"),
            "url":        issue.get("permalink", ""),
            "project":    sentry_event.get("actor", {}).get("name", ""),
            "first_seen": issue.get("firstSeen", ""),
            "platform":   issue.get("platform", "python"),
            "stacktrace": self._extract_stacktrace(issue),
        }

    def _extract_stacktrace(self, issue: dict) -> str:
        try:
            frames = (
                issue.get("entries", [{}])[0]
                    .get("data", {})
                    .get("values", [{}])[0]
                    .get("stacktrace", {})
                    .get("frames", [])
            )
            lines: List[str] = []
            for frame in frames[-5:]:  # innermost 5 frames are most diagnostic
                lines.append(
                    f"  File {frame.get('filename','?')} "
                    f"line {frame.get('lineNo','?')} "
                    f"in {frame.get('function','?')}"
                )
                for _, src_line in frame.get("context", []):
                    lines.append(f"    {src_line}")
            return "\n".join(lines)
        except Exception:
            return ""

    # ── reflex arc ────────────────────────────────────────────────────────────

    async def trigger_high_priority_reflex(
        self,
        pain_signal: dict,
        mission_id: str,
    ) -> str:
        """
        Fires the On-Call Auditor agent as a High_Priority_Reflex.
        Imports synaptic.dispatch lazily to avoid circular import at module load.
        Returns the raw fix output from the security agent.
        """
        from synaptic import dispatch  # lazy — avoids circular import at load time

        directive = (
            "[NOCICEPTOR_ALERT] Production runtime error detected.\n\n"
            f"Error : {pain_signal['title']}\n"
            f"Culprit: {pain_signal['culprit']}\n"
            f"Level  : {pain_signal['level']}\n\n"
            f"Stacktrace:\n{pain_signal['stacktrace']}\n\n"
            "DIRECTIVE: Locate the source file, diagnose the root cause, "
            "and produce a corrected version. Output the complete fixed file "
            "prefixed with 'FILE: path/to/file.py'."
        )
        synaptic_log.warning(
            f"[Nociceptor] High_Priority_Reflex → {pain_signal['title']}"
        )
        return await dispatch(
            objective=directive,
            mission_id=mission_id,
            agent_override="security",
        )

    async def dispatch_github_heal(
        self,
        file_path: str,
        fixed_content: str,
        repo: str,
        branch: str = "main",
        commit_message: str = "fix(nociceptor): autonomous self-heal via Synapticity",
    ) -> str:
        """
        Commits the healed file via the GitHub REST API.
        GitHub Actions CI/CD picks it up automatically.
        Returns the HTML URL of the commit.
        """
        if not settings.GITHUB_TOKEN:
            raise ConfigurationError("GITHUB_TOKEN required for GitHub heal dispatch")

        headers = {
            "Authorization": f"token {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        api_base = (
            f"https://api.github.com/repos/{settings.GITHUB_USER}/{repo}"
        )

        # Fetch current SHA — required by the GitHub Contents API to update a file
        get_resp = await self._http.get(
            f"{api_base}/contents/{file_path}",
            headers=headers,
            params={"ref": branch},
        )
        current_sha = (
            get_resp.json().get("sha", "") if get_resp.status_code == 200 else ""
        )

        body: dict = {
            "message": commit_message,
            "content": base64.b64encode(fixed_content.encode()).decode(),
            "branch": branch,
        }
        if current_sha:
            body["sha"] = current_sha

        put_resp = await self._http.put(
            f"{api_base}/contents/{file_path}", headers=headers, json=body
        )
        if put_resp.status_code not in (200, 201):
            raise WorkflowError(
                f"[Nociceptor] GitHub commit failed ({put_resp.status_code}): "
                f"{put_resp.text}"
            )

        commit_url = put_resp.json().get("commit", {}).get("html_url", "")
        synaptic_log.info(f"[Nociceptor] Heal committed to GitHub: {commit_url}")
        return commit_url

    async def resolve_sentry_issue(self, issue_id: str) -> bool:
        """Marks a Sentry issue resolved after a successful autonomous heal."""
        if not self._auth_token or not self._org_slug:
            synaptic_log.warning(
                "[Nociceptor] Sentry credentials missing — cannot auto-resolve"
            )
            return False
        resp = await self._http.put(
            f"{self._SENTRY_API}/issues/{issue_id}/",
            headers={"Authorization": f"Bearer {self._auth_token}"},
            json={"status": "resolved"},
        )
        resolved = resp.status_code == 200
        if resolved:
            synaptic_log.info(f"[Nociceptor] Sentry issue {issue_id} auto-resolved")
        return resolved

    async def aclose(self) -> None:
        await self._http.aclose()

    async def health_check(self) -> dict:
        if not self._auth_token:
            return {"organ": "nociceptor", "status": "unconfigured"}
        try:
            resp = await self._http.get(
                f"{self._SENTRY_API}/organizations/",
                headers={"Authorization": f"Bearer {self._auth_token}"},
            )
            status = "healthy" if resp.status_code == 200 else "degraded"
            return {"organ": "nociceptor", "status": status}
        except Exception as exc:
            return {"organ": "nociceptor", "status": "degraded", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ORGAN 4 — SENSORY INPUT  (Vision Data)
# PostHog session replays → frustration / success signals → synaptic weight
# adjustment in performance_metrics.json.  The PM agent watches this data to
# evolve UI designs: high rage-click pages get redesigned, high-conversion
# patterns get reinforced (Darwinian feedback loop).
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PostHogSensoryFeedback:
    """
    Vision Data: turns PostHog event streams into evolutionary pressure on agents.

    Frustration signals (rage clicks, dead clicks, abandonment) reduce the
    synaptic weight of the responsible agent/design.
    Success signals (conversions, goal completions) raise it.
    Weights are persisted in workspace/performance_metrics.json and read by
    IntelligenceRouter at model selection time.
    """

    _FRUSTRATION = frozenset({"$rageclick", "dead_click", "session_abandoned", "error_occurred"})
    _SUCCESS      = frozenset({"goal_completed", "purchase_completed", "signup_completed", "form_submitted"})

    def __init__(self) -> None:
        self._api_key    = os.getenv("POSTHOG_PERSONAL_API_KEY", "")
        self._project_id = os.getenv("POSTHOG_PROJECT_ID", "")
        self._host       = os.getenv("POSTHOG_HOST", "https://us.posthog.com")
        self._http       = httpx.AsyncClient(timeout=30)

    # ── event queries ─────────────────────────────────────────────────────────

    async def _query_events(
        self, event_names: List[str], hours_back: int
    ) -> List[dict]:
        if not self._api_key or not self._project_id:
            return []
        after_dt = (
            datetime.datetime.utcnow() - datetime.timedelta(hours=hours_back)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        resp = await self._http.get(
            f"{self._host}/api/projects/{self._project_id}/events/",
            headers={"Authorization": f"Bearer {self._api_key}"},
            params={
                "event__in": ",".join(event_names),
                "after":     after_dt,
                "limit":     500,
            },
        )
        if resp.status_code != 200:
            synaptic_log.warning(
                f"[Sensory] PostHog query failed {resp.status_code}: {resp.text[:120]}"
            )
            return []
        return resp.json().get("results", [])

    async def get_frustration_signals(self, hours_back: int = 24) -> List[dict]:
        """Returns rage-click and abandonment events as structured pain signals."""
        raw = await self._query_events(list(self._FRUSTRATION), hours_back)
        return [
            {
                "type":        "frustration",
                "event":       e.get("event"),
                "timestamp":   e.get("timestamp"),
                "distinct_id": e.get("distinct_id"),
                "page":        e.get("properties", {}).get("$current_url", ""),
                "element":     e.get("properties", {}).get("$el_text", ""),
            }
            for e in raw
        ]

    async def get_success_signals(self, hours_back: int = 24) -> List[dict]:
        """Returns conversion and goal-completion events for positive reinforcement."""
        raw = await self._query_events(list(self._SUCCESS), hours_back)
        return [
            {
                "type":        "success",
                "event":       e.get("event"),
                "timestamp":   e.get("timestamp"),
                "distinct_id": e.get("distinct_id"),
            }
            for e in raw
        ]

    # ── weight adjustment ─────────────────────────────────────────────────────

    async def adjust_synaptic_weights(
        self,
        agent_name: str,
        signal_type: str,   # "positive" | "negative"
        magnitude: float,   # 0.0–1.0
    ) -> None:
        """
        Mutates the synaptic_weights dict inside performance_metrics.json.
        Weights are clamped to [0.1, 2.0] so no agent is permanently silenced
        or given unbounded advantage.

        IntelligenceRouter reads this dict when selecting primary vs fallback model.
        """
        metrics_path = os.path.join(settings.WORKSPACE_PATH, "performance_metrics.json")
        try:
            with open(metrics_path, "r", encoding="utf-8") as fh:
                metrics: dict = json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            metrics = {}

        weights = metrics.setdefault("synaptic_weights", {})
        current = weights.get(agent_name, 1.0)
        delta   = magnitude * (0.1 if signal_type == "positive" else -0.1)
        updated = round(max(0.1, min(2.0, current + delta)), 3)
        weights[agent_name] = updated
        metrics["synaptic_weights"] = weights

        with open(metrics_path, "w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2)

        synaptic_log.info(
            f"[Sensory] {agent_name} weight {current:.3f} → {updated:.3f} "
            f"({signal_type}, magnitude={magnitude:.2f})"
        )

    # ── reporting ─────────────────────────────────────────────────────────────

    async def generate_vision_report(self, hours_back: int = 24) -> str:
        """Produces a PM-readable UX health report for the current observation window."""
        frustrations = await self.get_frustration_signals(hours_back)
        successes    = await self.get_success_signals(hours_back)

        total = len(frustrations) + len(successes)
        ratio = len(successes) / total if total else 0.0

        # Aggregate frustration by page
        page_freq: Dict[str, int] = {}
        for s in frustrations:
            page = s.get("page") or "unknown"
            page_freq[page] = page_freq.get(page, 0) + 1

        top_pages = sorted(page_freq.items(), key=lambda x: -x[1])[:5]

        lines = [
            f"## PostHog Vision Report (last {hours_back}h)",
            "",
            f"**Frustration signals**: {len(frustrations)}",
        ]
        for page, count in top_pages:
            lines.append(f"  - `{page}`: {count} frustration event(s)")
        lines += [
            "",
            f"**Success signals**: {len(successes)}",
            f"**Health ratio**  : {ratio:.1%}",
            "",
            "> Synaptic weight adjustments will be applied automatically." if total else
            "> No PostHog events found — check POSTHOG_PROJECT_ID and API key.",
        ]
        return "\n".join(lines)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def health_check(self) -> dict:
        if not self._api_key:
            return {"organ": "sensory", "status": "unconfigured"}
        try:
            resp = await self._http.get(
                f"{self._host}/api/projects/",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            status = "healthy" if resp.status_code == 200 else "degraded"
            return {"organ": "sensory", "status": status}
        except Exception as exc:
            return {"organ": "sensory", "status": "degraded", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ORGAN 5a — EFFERENT PATHWAY  (Outbound Synapse)
# Resend: structured mission reports and heal notifications via transactional email.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ResendSynapse:
    """
    Efferent synapse: dispatches structured emails via the Resend transactional API.
    Used for mission completion reports and autonomous-heal notifications.
    """

    _RESEND_API = "https://api.resend.com/emails"

    def __init__(self) -> None:
        self._api_key   = os.getenv("RESEND_API_KEY", "")
        self._from_addr = os.getenv("RESEND_FROM_EMAIL", "synapticity@noreply.ai")
        self._http      = httpx.AsyncClient(timeout=30)

    async def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> str:
        """Low-level email dispatch. Returns the Resend email ID."""
        if not self._api_key:
            raise ConfigurationError("RESEND_API_KEY not configured")

        payload: dict = {
            "from":    self._from_addr,
            "to":      [to] if isinstance(to, str) else to,
            "subject": subject,
            "html":    html_body,
        }
        if text_body:
            payload["text"] = text_body

        resp = await self._http.post(
            self._RESEND_API,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type":  "application/json",
            },
            json=payload,
        )
        if resp.status_code not in (200, 201):
            raise WorkflowError(
                f"[Efferent] Resend failed ({resp.status_code}): {resp.text}"
            )
        email_id = resp.json().get("id", "")
        synaptic_log.info(f"[Efferent] Email dispatched via Resend: {email_id}")
        return email_id

    async def send_mission_report(
        self,
        mission_id: str,
        to_email: str,
        summary: str,
        metrics: Optional[dict] = None,
    ) -> str:
        """Sends a structured mission completion report."""
        metrics_html = ""
        if metrics:
            rows = "".join(
                f"<tr><td style='padding:4px 8px'>{k}</td>"
                f"<td style='padding:4px 8px'><b>{v}</b></td></tr>"
                for k, v in metrics.items()
            )
            metrics_html = (
                "<table border='1' cellspacing='0' style='border-collapse:collapse'>"
                "<tr><th>Metric</th><th>Value</th></tr>"
                f"{rows}</table>"
            )

        html = f"""
        <html><body style="font-family:monospace;max-width:700px;margin:auto">
        <h2 style="color:#1a1a2e">Synapticity Mission Report</h2>
        <p><b>Mission ID:</b> <code>{mission_id}</code></p>
        <hr/>
        <h3>Summary</h3>
        <pre style="background:#f4f4f4;padding:12px;border-radius:4px">{summary}</pre>
        {metrics_html}
        <hr/>
        <small style="color:#888">
          Generated by Synapticity Neuromorphic Framework v{settings.VERSION}
        </small>
        </body></html>
        """
        return await self.send(
            to=to_email,
            subject=f"[Synapticity] Mission Complete: {mission_id}",
            html_body=html,
        )

    async def send_heal_notification(
        self,
        error_title: str,
        fix_summary: str,
        to_email: str,
        commit_url: str = "",
    ) -> str:
        """Notifies the team that the autonomous self-healing cycle succeeded."""
        commit_link = (
            f'<p><a href="{commit_url}" style="color:#0066cc">View Commit →</a></p>'
            if commit_url else ""
        )
        html = f"""
        <html><body style="font-family:monospace;max-width:700px;margin:auto">
        <h2 style="color:#1a1a2e">Synapticity Auto-Heal Report</h2>
        <p style="color:#2e7d32"><b>Status: HEALED</b></p>
        <h3>Error</h3>
        <pre style="background:#fff3e0;padding:12px;border-radius:4px">{error_title}</pre>
        <h3>Fix Applied</h3>
        <pre style="background:#e8f5e9;padding:12px;border-radius:4px">{fix_summary[:1200]}</pre>
        {commit_link}
        <hr/>
        <small style="color:#888">Autonomous heal by Synapticity Nociceptor</small>
        </body></html>
        """
        return await self.send(
            to=to_email,
            subject=f"[Synapticity] Auto-Heal: {error_title[:60]}",
            html_body=html,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def health_check(self) -> dict:
        return {
            "organ":  "efferent_synapse",
            "status": "healthy" if self._api_key else "unconfigured",
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ORGAN 5b — EFFERENT REFLEX  (Biological Alarm)
# Twilio: if the self-healing loop fails 3 consecutive times, place an emergency
# voice call to the human administrator.  SMS is used for non-critical escalations.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TwilioReflex:
    """
    Biological Alarm: escalates to human via Twilio voice call or SMS when the
    autonomous healing loop exceeds its failure threshold.

    Failure counting is in-process.  For multi-instance deployments wire
    GlobalMetabolicLock Redis to share the counter.
    """

    FAILURE_THRESHOLD = 3

    def __init__(self) -> None:
        self._account_sid  = os.getenv("TWILIO_ACCOUNT_SID", "")
        self._auth_token   = os.getenv("TWILIO_AUTH_TOKEN", "")
        self._from_number  = os.getenv("TWILIO_FROM_NUMBER", "")
        self._admin_number = os.getenv("TWILIO_ADMIN_NUMBER", "")
        self._http         = httpx.AsyncClient(timeout=30)
        self._failure_count = 0
        # Cached at init — credentials are immutable after construction
        self._cached_auth_header: Dict[str, str] = (
            {
                "Authorization": "Basic " + base64.b64encode(
                    f"{self._account_sid}:{self._auth_token}".encode()
                ).decode()
            }
            if self._account_sid and self._auth_token else {}
        )

    @property
    def _api_base(self) -> str:
        return f"https://api.twilio.com/2010-04-01/Accounts/{self._account_sid}"

    def _auth_header(self) -> dict:
        return self._cached_auth_header

    async def aclose(self) -> None:
        await self._http.aclose()

    # ── failure tracking ──────────────────────────────────────────────────────

    async def record_heal_failure(self) -> int:
        """Increments failure counter. Returns the updated count."""
        self._failure_count += 1
        synaptic_log.warning(
            f"[Reflex] Self-heal failure #{self._failure_count} "
            f"(threshold={self.FAILURE_THRESHOLD})"
        )
        return self._failure_count

    def reset_failure_count(self) -> None:
        """Resets counter after a successful heal — prevents stale alarms."""
        self._failure_count = 0

    async def check_and_fire_alarm(self, context: str) -> bool:
        """
        Evaluates whether the failure threshold is met and fires the biological
        alarm if so.  Returns True if the alarm was triggered.
        """
        if self._failure_count >= self.FAILURE_THRESHOLD:
            await self.trigger_biological_alarm(context)
            self._failure_count = 0  # reset so we don't spam
            return True
        return False

    # ── outbound calls ────────────────────────────────────────────────────────

    async def trigger_biological_alarm(self, context: str) -> str:
        """
        Places an emergency voice call to the administrator via Twilio
        Programmable Voice using inline TwiML.
        Returns the Twilio Call SID.
        """
        self._assert_credentials()
        safe_context = context[:200].replace("&", "and").replace("<", "[").replace(">", "]")
        twiml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            "<Say voice='alice'>"
            f"Synapticity critical alert. The autonomous self-healing loop has failed "
            f"{self.FAILURE_THRESHOLD} consecutive times. "
            f"Context: {safe_context}. "
            "Immediate human intervention is required."
            "</Say>"
            "<Pause length='2'/>"
            f"<Say voice='alice'>Repeating: {safe_context[:100]}</Say>"
            "</Response>"
        )
        resp = await self._http.post(
            f"{self._api_base}/Calls.json",
            headers=self._auth_header(),
            data={
                "From":   self._from_number,
                "To":     self._admin_number,
                "Twiml":  twiml,
            },
        )
        if resp.status_code not in (200, 201):
            raise WorkflowError(
                f"[Reflex] Twilio voice call failed ({resp.status_code}): {resp.text}"
            )
        call_sid = resp.json().get("sid", "")
        synaptic_log.critical(
            f"[Reflex] BIOLOGICAL ALARM FIRED — Twilio Call SID: {call_sid}"
        )
        return call_sid

    async def send_sms_alert(self, message: str, to: Optional[str] = None) -> str:
        """Sends a non-critical SMS escalation. Returns the Twilio Message SID."""
        self._assert_credentials(require_admin=False)
        target = to or self._admin_number
        resp = await self._http.post(
            f"{self._api_base}/Messages.json",
            headers=self._auth_header(),
            data={
                "From": self._from_number,
                "To":   target,
                "Body": f"[Synapticity] {message}"[:1600],
            },
        )
        if resp.status_code not in (200, 201):
            raise WorkflowError(
                f"[Reflex] Twilio SMS failed ({resp.status_code}): {resp.text}"
            )
        return resp.json().get("sid", "")

    def _assert_credentials(self, require_admin: bool = True) -> None:
        missing = [
            k for k, v in {
                "TWILIO_ACCOUNT_SID": self._account_sid,
                "TWILIO_AUTH_TOKEN":  self._auth_token,
                "TWILIO_FROM_NUMBER": self._from_number,
                **({"TWILIO_ADMIN_NUMBER": self._admin_number} if require_admin else {}),
            }.items()
            if not v
        ]
        if missing:
            raise ConfigurationError(
                f"Twilio not fully configured. Missing: {', '.join(missing)}"
            )

    async def health_check(self) -> dict:
        if not self._account_sid:
            return {"organ": "efferent_reflex", "status": "unconfigured"}
        try:
            resp = await self._http.get(
                f"{self._api_base}.json", headers=self._auth_header()
            )
            status = "healthy" if resp.status_code == 200 else "degraded"
            return {"organ": "efferent_reflex", "status": status}
        except Exception as exc:
            return {"organ": "efferent_reflex", "status": "degraded", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MASTER INTERFACE
# Neurons NEVER import individual organ classes — they interact exclusively
# through SynapticOrganInterface.  This indirection allows any organ to be
# swapped (e.g. Resend → SendGrid, Upstash → local Redis) without touching
# any agent code.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SynapticOrganInterface:
    """
    Central nervous system gateway for the Production Synapse Layer.

    Initialisation is fault-tolerant: organs with missing credentials are
    skipped and logged rather than crashing the whole system.  Call
    health_check() to see which organs are online.

    Usage
    ─────
        organs = SynapticOrganInterface()
        row_id = await organs.hippocampus.store_reflection(...)
        fired  = await organs.efferent_reflex.check_and_fire_alarm(context)
    """

    def __init__(self, enabled: Optional[List[str]] = None) -> None:
        """
        enabled: subset of organ names to activate. Defaults to all five.
        Valid names: "metabolism", "hippocampus", "nociceptor", "sensory", "efferent"
        "efferent" is a convenience alias that enables both efferent_synapse and efferent_reflex.
        """
        targets: set = set(enabled or ["metabolism", "hippocampus", "nociceptor", "sensory", "efferent"])
        # Expand the "efferent" alias so Resend and Twilio init independently
        if "efferent" in targets:
            targets.discard("efferent")
            targets.update({"efferent_synapse", "efferent_reflex"})

        self.metabolism:       Optional[GlobalMetabolicLock]   = None
        self.hippocampus:      Optional[SupabaseMemoryProvider] = None
        self.nociceptor:       Optional[SentryNociceptor]       = None
        self.sensory:          Optional[PostHogSensoryFeedback] = None
        self.efferent_synapse: Optional[ResendSynapse]          = None
        self.efferent_reflex:  Optional[TwilioReflex]           = None
        self._init_errors: Dict[str, str] = {}

        # Each organ is registered separately so one failure never blocks another
        _registry: Dict[str, callable] = {
            "metabolism":       lambda: setattr(self, "metabolism",       GlobalMetabolicLock()),
            "hippocampus":      lambda: setattr(self, "hippocampus",      SupabaseMemoryProvider()),
            "nociceptor":       lambda: setattr(self, "nociceptor",       SentryNociceptor()),
            "sensory":          lambda: setattr(self, "sensory",          PostHogSensoryFeedback()),
            "efferent_synapse": lambda: setattr(self, "efferent_synapse", ResendSynapse()),
            "efferent_reflex":  lambda: setattr(self, "efferent_reflex",  TwilioReflex()),
        }
        for name, init_fn in _registry.items():
            if name in targets:
                try:
                    init_fn()
                except ConfigurationError as exc:
                    self._init_errors[name] = str(exc)
                    synaptic_log.warning(f"[SynapticOrgan] {name} offline: {exc}")

    async def health_check(self) -> dict:
        """Returns a full status report for all configured organs."""
        organ_checks = [
            ("metabolism",      self.metabolism),
            ("hippocampus",     self.hippocampus),
            ("nociceptor",      self.nociceptor),
            ("sensory",         self.sensory),
            ("efferent_synapse", self.efferent_synapse),
            ("efferent_reflex",  self.efferent_reflex),
        ]
        results = {}
        for name, organ in organ_checks:
            if organ is None:
                results[name] = {
                    "status": "offline",
                    "error":  self._init_errors.get(name.split("_")[0], "not initialised"),
                }
            else:
                results[name] = await organ.health_check()

        healthy = sum(1 for v in results.values() if v.get("status") == "healthy")
        return {
            "framework":      "Synapticity Production Synapse Layer",
            "version":        settings.VERSION,
            "healthy_organs": f"{healthy}/{len(organ_checks)}",
            "organs":         results,
        }

    async def aclose(self) -> None:
        """Closes all open HTTP connections held by organs. Call on application shutdown."""
        for organ in (
            self.nociceptor,
            self.sensory,
            self.efferent_synapse,
            self.efferent_reflex,
        ):
            if organ is not None and hasattr(organ, "aclose"):
                try:
                    await organ.aclose()
                except Exception:
                    pass
