# RAG Evaluation

## Test 1 - Direct Answer

Query:
How long are database backups retained?

Top K Results:

| Rank | Source | Chunk ID | Score | Retrieved Text |
|---|---|---:|---:|---|
| 1 | database.md | 3 | 0.7153 | Backups are retained for 30 days. |
| 2 | database.md | 2 | 0.5252 | Production database backups run automatically every night at 2:00 AM UTC. |
| 3 | database.md | 0 | 0.4274 | Database Operations |

Final Answer:
The database backups are retained for 30 days.

Human Judgment:
PASS — The correct supporting chunk was retrieved as Rank 1, and the final answer was grounded in the retrieved evidence.

## Test 2 - Two-Chunk Question

Query:
What should engineers verify before deploying to production, and how should secrets be handled?

Top K Results:

| Rank | Source | Chunk ID | Score | Retrieved Text |
|---|---|---:|---:|---|
| 1 | security.md | 2 | 0.5384 | API keys and database passwords must be stored using environment variables or a secret management system. |
| 2 | deployment.md | 5 | 0.5296 | Environment variables must be stored outside the source code. Secrets such as API keys must never be committed to Git. |
| 3 | security.md | 4 | 0.4932 | Access to production systems should follow the principle of least privilege. |
| 4 | security.md | 1 | 0.4643 | Employees must use multi-factor authentication for production systems. |
| 5 | database.md | 5 | 0.4562 | Database migrations must be tested in staging before production. |

Final Answer:
Engineers should verify that database migrations have been tested in staging before deploying to production. Secrets such as API keys and database passwords must be stored using environment variables or a secret management system, and environment variables must be stored outside the source code. Secrets should never be committed to Git.

Human Judgment:
PARTIAL FAIL — The system correctly retrieved and answered the secrets-handling portion, but it failed to retrieve the strongest deployment evidence: "Before deployment, all automated tests must pass."

Failure Type:
Retrieval failure. Increasing top_k from 3 to 5 did not recover the expected deployment chunk, so the issue is not only the Top-K cutoff. The multi-part query may be difficult for a single query embedding, and the current paragraph-level chunking may also affect ranking quality.

## Test 3 - No-Answer Question

Query:
What AWS region is the application deployed in?

Top K Results:

| Rank | Source | Chunk ID | Score | Retrieved Text |
|---|---|---:|---:|---|
| 1 | deployment.md | 0 | 0.5058 | Application Deployment |
| 2 | deployment.md | 1 | 0.3754 | The production application runs in Docker containers. |
| 3 | database.md | 1 | 0.3687 | The application uses PostgreSQL as its primary database. |
| 4 | deployment.md | 3 | 0.3253 | The application listens on port 8000. |
| 5 | deployment.md | 4 | 0.2679 | Before deployment, all automated tests must pass. |

Final Answer:
I don't know based on the provided documents.

Human Judgment:
PASS — The retrieved chunks were related to deployment but did not contain an AWS region. The model correctly refused to guess and did not hallucinate an unsupported answer.

## Test 4 - Semantic Match with Different Keywords

Query:
How should the company protect sensitive credentials?

Top K Results:

| Rank | Source | Chunk ID | Score | Retrieved Text |
|---|---|---:|---:|---|
| 1 | security.md | 2 | 0.5260 | API keys and database passwords must be stored using environment variables or a secret management system. |
| 2 | security.md | 1 | 0.5084 | Employees must use multi-factor authentication for production systems. |
| 3 | security.md | 0 | 0.4971 | Security Policy |
| 4 | security.md | 4 | 0.4606 | Access to production systems should follow the principle of least privilege. |
| 5 | deployment.md | 5 | 0.3992 | Environment variables must be stored outside the source code. Secrets such as API keys must never be committed to Git. |

Final Answer:
The company should protect sensitive credentials by storing API keys and database passwords using environment variables or a secret management system. Additionally, environment variables must be stored outside the source code, and secrets such as API keys must never be committed to Git.

Human Judgment:
PASS — The retriever successfully matched the semantic meaning of "protect sensitive credentials" even though the query used different wording from the source documents. The final answer was supported by the retrieved evidence.

## Test 5 - Easy Wrong-Retrieval Question

Query:
If the application loses access to its database, what should engineers check first?

Top K Results:

| Rank | Source | Chunk ID | Score | Retrieved Text |
|---|---|---:|---:|---|
| 1 | database.md | 4 | 0.7130 | If the database becomes unavailable, engineers should first check the database service status and connection credentials. |
| 2 | database.md | 0 | 0.4470 | Database Operations |
| 3 | database.md | 1 | 0.4414 | The application uses PostgreSQL as its primary database. |
| 4 | security.md | 2 | 0.3804 | API keys and database passwords must be stored using environment variables or a secret management system. |
| 5 | deployment.md | 0 | 0.3774 | Application Deployment |

Final Answer:
Engineers should first check the database service status and connection credentials.

Human Judgment:
PASS — The retriever ranked the correct troubleshooting chunk first even though other chunks contained related terms such as database, credentials, and security. The final answer was directly supported by the retrieved evidence.

## Failure Analysis

The main failure case occurred in Test 2:

**Query:**  
What should engineers verify before deploying to production, and how should secrets be handled?

The system successfully retrieved the chunks related to secret handling, including storing API keys and database passwords in environment variables or a secret management system and not committing secrets to Git.

However, it failed to retrieve the most relevant deployment chunk:

> Before deployment, all automated tests must pass.

Even after increasing `top_k` from 3 to 5, this chunk was still not included in the retrieved results. Instead, the retriever returned other production-related chunks such as least-privilege access, multi-factor authentication, and database migration testing.

Because the correct deployment evidence was not included in the context, the LLM generated an answer using the available retrieved evidence. The answer was supported by the retrieved chunks, but it did not fully answer the intended deployment part of the question.

I classify this mainly as a **retrieval failure** rather than a generation failure. The LLM did not hallucinate unsupported information; the problem happened earlier because the retriever did not rank the correct deployment chunk highly enough.

One possible reason is that the query contains two different intents: deployment verification and secret handling. A single query embedding may not represent both intents equally well. The current paragraph-based chunking strategy may also affect retrieval quality because each chunk is short and contains only one small piece of information.

Possible improvements include:
- splitting multi-part questions into separate retrieval queries;
- experimenting with different chunk sizes or chunk overlap;
- testing different values of `top_k`;
- adding a reranking step after the initial FAISS retrieval.