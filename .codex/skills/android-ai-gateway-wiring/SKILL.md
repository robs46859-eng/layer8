---
name: android-ai-gateway-wiring
description: Wire an Android Compose app to a Layer8 AI gateway using a provider (Gemini, OpenAI, etc.), a tenant-scoped API key, and OkHttp. Use when adding AI chat to an Android app that routes through Layer8 instead of calling an AI provider directly.
---

# Android → Layer8 AI Gateway Wiring

Use this skill when an Android Jetpack Compose app needs AI chat functionality routed through a Layer8 gateway instance rather than calling Gemini or OpenAI directly.

This pattern gives you:
- One API key in the app, provider credentials stay server-side
- Rate limiting, caching, and audit logging for free
- Swap AI providers without touching the Android app
- Per-tenant usage tracking from day one

---

## The Pattern

```
Android app (OkHttp)
  → POST /v1/proxy/infer  (X-API-Key: tenant key)
    → Layer8 pipeline (auth → rate limit → cache → provider → audit)
      → Gemini / OpenAI / other provider
```

---

## Layer8 Side

### 1. Add the provider

Create `app/providers/<name>.py` following the `ProviderAdapter` protocol in `app/providers/base.py`.

For any provider with an OpenAI-compatible endpoint (including Gemini):

```python
class GeminiProvider:
    name = "gemini"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def infer(self, context: RequestContext) -> InferenceResponse:
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY not set")

        messages = [{"role": "system", "content": YOUR_SYSTEM_PROMPT}]
        messages += [m.model_dump() for m in context.payload.messages]

        async with httpx.AsyncClient(base_url=self.BASE_URL, timeout=30.0) as client:
            response = await client.post(
                "chat/completions",
                headers={"Authorization": f"Bearer {self.settings.gemini_api_key}"},
                json={"model": context.payload.model, "messages": messages, "stream": False},
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]["message"]["content"]
        usage  = data.get("usage", {})
        return InferenceResponse(
            request_id=context.request_id,
            tenant_id=context.tenant_id or "unknown",
            provider=self.name,
            model=context.payload.model,
            output_text=choice,
            usage=Usage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            ),
        )
```

### 2. Register in config

Add the API key field to `app/core/config.py`:

```python
gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
```

### 3. Register in pipeline

In `app/core/pipeline.py`, import and add to the registry:

```python
from app.providers.gemini import GeminiProvider

provider_registry = ProviderRegistry({
    "mock":   MockProvider(),
    "openai": OpenAIChatProvider(settings),
    "gemini": GeminiProvider(settings),
})
```

### 4. Set the key and restart

```bash
echo "GEMINI_API_KEY=your_key_here" >> .env
pkill -f uvicorn
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

### 5. Provision a tenant and API key

```bash
# Create tenant
curl -X POST http://localhost:8000/admin/tenants \
  -H "Authorization: Bearer $ADMIN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"myapp","name":"My App","data_residency":"us"}'

# Create scoped API key — only allow the models the app needs
curl -X POST http://localhost:8000/admin/tenants/myapp/api-keys \
  -H "Authorization: Bearer $ADMIN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scopes":["inference:invoke"],"allowed_models":["gemini-2.0-flash","mock-echo"]}'
```

Save the returned `api_key` value — this goes in the Android app.

### 6. Smoke test

```bash
curl -X POST http://localhost:8000/v1/proxy/infer \
  -H "X-API-Key: <tenant_api_key>" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-2.0-flash","messages":[{"role":"user","content":"Hello"}]}'
```

Expect `output_text` in the response and all 9 stages in `stage_trace`.

---

## Android Side

### 1. Add OkHttp

In `gradle/libs.versions.toml`:
```toml
okhttp = "4.12.0"
...
okhttp = { group = "com.squareup.okhttp3", name = "okhttp", version.ref = "okhttp" }
```

In `app/build.gradle.kts`:
```kotlin
implementation(libs.okhttp)
```

### 2. Add permissions to AndroidManifest.xml

```xml
<uses-permission android:name="android.permission.INTERNET" />
<application
    android:usesCleartextTraffic="true"   <!-- remove in production, use HTTPS -->
    ...>
```

### 3. Config object

```kotlin
// network/Layer8Config.kt
object Layer8Config {
    const val BASE_URL = "http://your-server-ip:8000"  // use HTTPS in production
    const val API_KEY  = "ak_live_xxxx.yyyy"           // tenant key from step 5 above
    const val MODEL    = "gemini-2.0-flash"
}
```

### 4. ViewModel — HTTP call in a coroutine

```kotlin
// In your ViewModel (extends ViewModel so viewModelScope is available)
var chatMessages by mutableStateOf(listOf<ChatMessage>())
var isAiTyping   by mutableStateOf(false)

private val httpClient   = OkHttpClient()
private val jsonMediaType = "application/json".toMediaType()

fun sendChatMessage(text: String) {
    chatMessages = chatMessages + ChatMessage(id = "u${chatMessages.size}", role = "user", text = text)
    isAiTyping = true
    viewModelScope.launch {
        try {
            val reply = withContext(Dispatchers.IO) { callLayer8() }
            chatMessages = chatMessages + ChatMessage(id = "m${chatMessages.size}", role = "model", text = reply)
        } catch (e: Exception) {
            chatMessages = chatMessages + ChatMessage(id = "err${chatMessages.size}", role = "model",
                text = "Couldn't reach AI. Check your connection and server. 💛")
        } finally {
            isAiTyping = false
        }
    }
}

private fun callLayer8(): String {
    val messagesArray = JSONArray()
    chatMessages.takeLast(12).forEach { msg ->
        messagesArray.put(JSONObject().apply {
            put("role", msg.role)
            put("content", msg.text)
        })
    }
    val body = JSONObject().apply {
        put("model", Layer8Config.MODEL)
        put("messages", messagesArray)
    }.toString()

    val request = Request.Builder()
        .url("${Layer8Config.BASE_URL}/v1/proxy/infer")
        .addHeader("X-API-Key", Layer8Config.API_KEY)
        .post(body.toRequestBody(jsonMediaType))
        .build()

    httpClient.newCall(request).execute().use { response ->
        if (!response.isSuccessful) throw RuntimeException("Layer8 HTTP ${response.code}")
        return JSONObject(response.body?.string()!!).getString("output_text")
    }
}
```

### 5. Typing indicator in Compose

```kotlin
if (isAiTyping) {
    Row {
        repeat(3) { i ->
            val alpha by rememberInfiniteTransition(label = "dot$i").animateFloat(
                initialValue = 0.3f, targetValue = 1f,
                animationSpec = infiniteRepeatable(tween(600, delayMillis = i * 200), RepeatMode.Reverse),
                label = "dot$i",
            )
            Box(Modifier.size(8.dp).clip(CircleShape).background(primaryColor.copy(alpha = alpha)))
        }
    }
}
```

---

## Production Checklist

- [ ] Move `BASE_URL` to HTTPS (Cloudflare Tunnel or a real domain with TLS)
- [ ] Remove `android:usesCleartextTraffic="true"` from the manifest
- [ ] Move `API_KEY` out of source — use `local.properties` → `BuildConfig`
- [ ] Rotate the `ADMIN_API_TOKEN` in `.env` from the default
- [ ] Set `GEMINI_API_KEY` (or other provider key) in a real secret manager, not plain `.env`
- [ ] Enable `STARTUP_CHECKS_STRICT=true` in production

## Trigger Examples

- "Wire the Android chat screen to Layer8"
- "Add Gemini AI to this Android app through the gateway"
- "Connect a mobile app to Layer8 for AI inference"
- "Add a new provider to Layer8 and give an Android tenant a key"
