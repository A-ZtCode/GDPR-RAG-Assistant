# Building a Production RAG Assistant for GDPR
## Part 1: Foundations, Decisions, and One API Key I Nearly Leaked

*This is the first post in a series on building a production-oriented Retrieval-Augmented Generation (RAG) system for GDPR regulatory Q&A. Across the series I'll cover architecture, chunking strategy, retrieval, guardrails, evaluation, and deployment. Code, decisions, and mistakes all in public.*

---

## Why this project

Hiring for AI-related engineering roles in 2026 is dominated by two capabilities: RAG and agentic AI workflows. Every senior ML engineering role I've looked at in the last few months, particularly in regulated financial services, mentions those two alongside classical MLOps, model monitoring, and responsible AI. The pattern is consistent, and it maps well onto real business needs: enterprises want language models that can reason about their internal knowledge without hallucinating, and they want them wrapped in the kind of infrastructure that lets a compliance team sleep at night.

I need a portfolio piece that speaks directly to that shape of role. So I'm building one.

The project: a RAG assistant that answers questions about the General Data Protection Regulation (GDPR), grounded in the actual text of the regulation, with citations traceable back to specific articles. The sort of thing a compliance officer, a Data Protection Officer, or a developer trying to design a lawful data pipeline might actually use.

## What "production-oriented" means (and doesn't)

Most RAG projects on GitHub are demos. Someone chunks a PDF, throws embeddings into a vector store, wires up an LLM call, ships a Streamlit app, calls it done. That's a reasonable first pass, but it isn't what production means in an enterprise setting.

Production means, at minimum:

- The system is safe to hand to a user (input guardrails, refusal behaviour, PII handling)
- The system is honest about what it doesn't know (grounded citations, no hallucination)
- The system is measurable (an evaluation harness, not "looks good to me")
- The system is monitorable (traces, logs, cost tracking)
- The system is deployable and reproducible (CI, containers, dependency pinning)

I'm not building all of that in one sprint. Timeline is tight; I have a day job and other commitments. But I'm scoping every decision as if I were going to production, and I'm calling out where I've deferred something intentionally to make the timeline work. The finished MVP will have the production hooks in the right places, so extensions are additive rather than architectural rewrites.

An honest MVP with a live URL and a clear roadmap is a better portfolio piece than a half-finished "production system" pretending to be more than it is. I want to be able to defend every line of the README in interview.

## The end state, in one diagram

Six things happen at query time:

1. **Input guardrail**: rejects out-of-scope questions, strips PII, blocks prompt-injection attempts
2. **Retriever**: turns the question into an embedding vector, searches for the most similar chunks in the vector store
3. **Vector store**: holds pre-computed embeddings of GDPR text and returns the top matches
4. **LLM generation**: produces an answer using only the retrieved context
5. **Output validation**: checks the answer is grounded in the context, no leaked PII, no hallucinated citations
6. **Answer + citations**: what the user sees, with links back to specific GDPR articles

There's also a separate ingestion pipeline (run once, before any queries) and an evaluation loop (run during development, ideally continuously in production too). I'll cover both in later posts.

*[Insert architecture diagram here when publishing]*

## Three design decisions I made before writing any code

Every meaningful design decision I make on this project, I want to be able to defend. Here are the three I made upfront.

### Corpus: GDPR

99 articles. Well-structured. Publicly available on EUR-Lex. Universally recognisable. Small enough that ingestion runs in seconds; large enough that retrieval quality matters.

I considered FCA sourcebooks, which are closer to my day job in UK financial services, but decided against them for a first project. GDPR is more universally known, which makes the write-up more portable. If the project lands well, I can port the same architecture to FCA texts as a follow-up.

### LLM provider: Anthropic

Both Anthropic and OpenAI are reasonable choices. I picked Anthropic (Claude Sonnet 4.5) for two reasons. First, my early experiments suggested it handled the "answer only from the provided context, refuse otherwise" instruction pattern more consistently, and RAG systems live or die by that pattern. Second, the abstraction I'm building around the LLM call will make it trivial to swap providers. If a future comparison shows OpenAI performing better on my evaluation set, the change is a config file update.

The takeaway I want to internalise: don't couple your architecture to a specific model provider. That's true in any production system, and it's what an interviewer will expect you to say.

### Chunking strategy hypothesis: article-level

Chunking is the single highest-leverage design decision in a RAG pipeline, and it's the one most tutorials skip past. Split every 500 tokens and move on. That naive strategy is what makes most hobby RAG systems bad, because it cuts across the natural boundaries of the source document and produces incoherent chunks that neither retrieve well nor read well.

GDPR gives me natural boundaries almost for free. 99 numbered articles, each a self-contained rule, each with a title that summarises it. My hypothesis is that one chunk per article, with article number and title preserved as metadata, will outperform naive fixed-size splitting.

I say "hypothesis" because I don't yet know it's the right choice. Article 5 (principles) is short. Article 89 (safeguards for research) is quite long. Some articles may exceed the LLM's practical context budget when combined with other retrieved chunks and need further splitting. I'll validate the strategy against an evaluation set once I've built one.

## Setting up the environment

With the design decisions on paper, I moved to setup. Nothing glamorous here, but there are two decisions worth flagging for anyone following along or replicating the setup.

**Python 3.12 with a virtual environment.** Standard hygiene. `python -m venv .venv` in the project root, then `source .venv/bin/activate`. Every subsequent `pip install` lands inside `.venv/` and stays isolated from my system Python and from other projects. This is what makes the project reproducible: a new developer running `pip install -r requirements.txt` inside their own venv will get exactly the same packages.

**Git repository and a `.gitignore` file that treats secrets seriously.** The pattern I use:

```
# Environment variables and secrets
.env
.env.*
!.env.example
```

The rule `.env` catches the real secret file, `.env.*` catches variants like `.env.production` and `.env.local`, and `!.env.example` re-includes just the template. `.env.example` is a committed placeholder that documents which environment variables the project needs, with dummy values. `.env` is the real file with real secrets, and it never leaves my machine.

This template pattern is used by essentially every production Python codebase, and it's the safest way to onboard collaborators: they clone the repo, copy `.env.example` to `.env`, fill in their own credentials, and they're running.

## The security near-miss

Which brings me to the mistake worth writing about.

I created `.env.example` with the placeholder value, exactly as the pattern requires. Then, in a moment of not paying attention, I opened `.env.example` in my editor instead of `.env`, and pasted my real Anthropic API key into it. Then I ran the standard git commands to make my first commit.

```bash
git add .gitignore .env.example
git commit -m "Add gitignore and env template"
git push
```

`git push` failed:

```
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote:     - Push cannot contain secrets
remote:       —— Anthropic API Key —————————————————————————————————
```

GitHub's secret scanning caught the API key in the commit and rejected the push. The key never made it into the public repo. But GitHub's servers had already scanned the commit, so I treated the key as potentially exposed and rotated it immediately.

Three things I learned or re-learned from this:

**The template pattern doesn't protect you from your own inattention.** Gitignore rules only work if you put the secret in the right file. When you're moving fast between files with similar names, "the right file" is easy to get wrong. I now have a habit of running `git diff --cached` before every commit that touches config files, and reading what I'm about to push line by line.

**Rotate first, fix later.** As soon as I saw the rejection message, my instinct was to fix the file and re-push. The correct instinct is to rotate the key first, because any exposure at all (even to a scanner) is enough to treat it as compromised. In an enterprise context this would be an incident report, a rotation ticket, and possibly a financial hit from someone running up API bills on the leaked key. Better to internalise that reflex on a personal project than in the first month of a new role.

**`git diff --cached` is your friend.** The staging area is a snapshot from when you ran `git add`, not a live view of your working files. If you edit a file after adding it, the diff will show the old (pre-edit) content until you `git add` again. This is a fiddly detail that trips up experienced engineers, and it's the reason I initially thought I'd fixed the file and hadn't. Read the diff, not the file. The diff is what's about to be pushed.

The tone in security-conscious teams is neither panicked nor blasé. It's a calm reflex: "we saw a secret exposure, we rotated, we fixed the config, we're done." That's the tone I want to build into my own habits, even when it's my project and there's no one to report to.

## Smoke testing the stack

Once the repo was clean and the new key was in `.env`, I wanted the smallest possible test that everything downstream would work: environment variable loading, SDK installation, API authentication, model response parsing. Ten lines of code:

```python
"""Smoke test: confirm we can call the Anthropic API."""

import os

from anthropic import Anthropic
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not found. Check your .env file."
        )

    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": "Say hello in exactly one short sentence.",
            }
        ],
    )

    print("Claude replied:")
    print(response.content[0].text)


if __name__ == "__main__":
    main()
```

Two small choices worth noting.

The explicit `if not api_key: raise` check is defensive, not clever. If the environment variable isn't loaded, this fails loudly with a clear message rather than sending a `None` to the SDK and getting a confusing authentication error two layers down the stack. Small habit, useful in every language, essential in production code where failure messages are often the only thing a user sees.

Reading `os.getenv` after `load_dotenv()` is the standard pattern for the `python-dotenv` library. `load_dotenv()` reads the `.env` file and injects its key-value pairs into the process's environment variables. From that point on, `os.getenv` finds them the same way it would find any system-level environment variable, which means the same code works in local development (values loaded from `.env`), in CI (values injected by the CI runner), and in production (values injected by the deployment platform). One code path, three environments.

Running the script printed:

```
Claude replied:
Hello!
```

Not exciting on the face of it, but that one line proved the entire pipeline: SDK installation, environment variable loading, API authentication, network path to Anthropic's servers, model call, response parsing, print to stdout. Every future piece of the project builds on top of this working foundation.

## What's next

The next post covers the ingestion pipeline: pulling the GDPR text from EUR-Lex, splitting it into article-level chunks, generating embeddings, and storing them in a vector database (Chroma). I'll go deep on the chunking strategy, including what happens when an article is too long for one chunk and how metadata like article number and title get carried through the pipeline for use in citations.

I'll also introduce the two concepts that make or break a RAG system: embeddings and cosine similarity. Both are less scary than they sound, and both come up in almost every interview question about RAG.

Follow along, star the repo, or roast my decisions. All useful. The repo is at [github.com/A-ZtCode/GDPR-RAG-Assistant](https://github.com/A-ZtCode/GDPR-RAG-Assistant).

---

*Feedback welcome. If you're building something similar or have thoughts on where I'm about to make a mistake, I'd rather hear it now than in an interview.*
