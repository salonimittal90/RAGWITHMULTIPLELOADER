Project Documentation
1. What this project does
This is a Python RAG app using:

FastAPI for HTTP endpoints
Vertex AI for embeddings and chat
MongoDB Atlas for vector storage
LangGraph / LangChain for retrieval and graph-based tool execution
It supports:

loading web pages or files into a vector store
asking questions against the indexed documents
checkpointing session state in MongoDB


2. Main components
main.py
Creates the FastAPI app
Adds CORS middleware
Includes three routers:
routes.loader_route for loading documents21`
routes.rag_route for asking questions
routes.checkpointer_route for checkpoint history


config.py
Loads .env
Creates Vertex AI clients:
ChatVertexAI for LLM
VertexAIEmbeddings for embeddings
Connects to MongoDB
Creates MongoDBAtlasVectorSearch as vector_store
Creates async MongoDB client aclient


.env
Contains project configuration values:

VERTEX_PROJECT
VERTEX_LOCATION
MONGODB_URI
DATABASE_NAME
COLLECTION_NAME
ATLAS_VECTOR_SEARCH_INDEX_NAME


3. Document loading flow
loader_route.py
Provides endpoints:

POST /load_url
loads a website
POST /load_file
uploads and loads PDF/DOCX/CSV/PPTX/image files
Both call:

repos.loader.load_and_index_documents(...)
loader.py
This is the ingestion pipeline:

Select loader by type:
WebBaseLoader for web
PyPDFLoader for PDF
Docx2txtLoader for DOCX
CSVLoader for CSV
UnstructuredPowerPointLoader for PPTX
GitLoader for git repos
UnstructuredFileLoader for images
Load documents
Split text into chunks using RecursiveCharacterTextSplitter
Add chunks to MongoDB vector store:
vector_store.add_documents(documents=all_splits)
So a load request creates embedded document vectors in MongoDB.

4. Question-answer flow
rag_route.py
Endpoint:

POST /ai/ask_question
It:

builds a config object with thread_id and user_email
creates a HumanMessage from the user query
calls async_graph.ainvoke(...)
returns the last message content from the graph response
rag_pipe.py
This defines the graph used by async_graph.

Key parts
State extends MessagesState
adds context: List[Document]
adds trace_id: str
retrieve(query)
runs vector_store.similarity_search(query, k=4)
returns a serialized string + the retrieved docs
query_or_respond(state)
binds the tool to the LLM
builds a prompt from state messages
calls llm_with_tools.invoke(prompt)
returns an LLM response as a tool/AI message
generate(state)
finds tool messages in state["messages"]
builds docs_content from tool messages
calls llm.invoke(prompt) for final answer
collects tool artifacts into context

Graph wiring
graph_builder = StateGraph(State)
Nodes:
query_or_respond
tools
generate
Entry point: query_or_respond
Conditional edge:
if tool needed, go to tools
then go to generate
Checkpointer:
uses AsyncMongoDBSaver with aclient
compiles into async_graph

5. Checkpointing and history
checkpointer_route.py
Provides endpoints:

GET /cp/latest_checkpoint
GET /cp/get_recent_threads
checkpointer.py
async_memory = AsyncMongoDBSaver(...)
CheckpointerService.get_latest_checkpoint(...)
fetches latest checkpoint for a thread/email
CheckpointerService.get_recent_threads()
lists recent thread IDs from Mongo
This stores graph checkpoints in MongoDB and lets you inspect recent sessions.

6. How the request flows end-to-end
Loading
Client calls POST /load_url or POST /load_file
loader_route calls load_and_index_documents
Loader reads source -> splits text -> stores vectors in Mongo

Asking:

Client calls POST /ai/ask_question
rag_route creates a HumanMessage
Calls async_graph.ainvoke(...)
query_or_respond runs retrieval tool
retrieve() searches Mongo vector DB
If results exist, tool output goes into graph
generate() produces final answer using retrieved context
Response returns to client

Thanks.


we are using ollama  software in place of gemini due to limit issue.
ollama is a software where we uses qwen llm model of Alibaba family.
