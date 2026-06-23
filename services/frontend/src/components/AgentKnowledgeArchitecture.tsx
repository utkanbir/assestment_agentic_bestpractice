/** Best-practice knowledge management architecture guide for Ajan Yönetimi */
import type { CSSProperties, ReactNode } from "react";

const EXAMPLE_EVENT_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890";

const EXAMPLE = {
  workstream: "kubernetes",
  question: "Kubernetes kullanmanın temel faydaları nelerdir?",
  answer: "Vendor bağımsız yazılım geliştirmek ve scale edebilmek",
  author: "consultant",
};

const EXAMPLE_SQL = `SELECT id, workstream, mode, question_text, answer_text,
       answer_author, consultant_id, created_at
FROM agent_learning_events
WHERE workstream = 'kubernetes'
  AND question_text LIKE '%temel faydalar%';

-- Örnek sonuç satırı:
-- id              | ${EXAMPLE_EVENT_ID}
-- workstream      | kubernetes
-- mode            | aaha
-- question_text   | ${EXAMPLE.question}
-- answer_text     | ${EXAMPLE.answer}
-- answer_author   | consultant
-- consultant_id   | <seçilen danışman UUID veya NULL>`;

const EXAMPLE_TURTLE = `@prefix aakp: <https://aakp.ai/ontology/assessment#> .

# Agent node
<https://aakp.ai/data/agent/kubernetes>
    a                           aakp:Task ;
    aakp:hasWorkstream          "kubernetes" .

# Training event (PostgreSQL id ile bağlı)
<https://aakp.ai/data/training/${EXAMPLE_EVENT_ID}>
    a                           aakp:TrainingInteraction ;
    aakp:forWorkstream          "kubernetes" ;
    aakp:trainingMode           "aaha" ;
    aakp:trainingQuestion       "${EXAMPLE.question}" ;
    aakp:trainingAnswer         "${EXAMPLE.answer}" ;
    aakp:answerAuthor           "consultant" ;
    aakp:pgId                   "${EXAMPLE_EVENT_ID}" .

# İlişki
<https://aakp.ai/data/agent/kubernetes>
    aakp:hasTrainingEvent       <https://aakp.ai/data/training/${EXAMPLE_EVENT_ID}> .

# Domain kavram linkleri (refersToConcept — kayıt sonrası otomatik)
<https://aakp.ai/data/training/${EXAMPLE_EVENT_ID}>
    aakp:refersToConcept        <https://aakp.ai/data/capability/container-platform> ;
    aakp:refersToConcept        <https://aakp.ai/data/theme/vendor-independence> ;
    aakp:refersToConcept        <https://aakp.ai/data/theme/horizontal-scalability> .`;

const EXAMPLE_QDRANT = `{
  "collection": "documents",
  "payload": {
    "event_id": "${EXAMPLE_EVENT_ID}",
    "workstream": "kubernetes",
    "mode": "aaha",
    "chunk_index": 0,
    "text": "Soru: ${EXAMPLE.question}\\nYanıt: ${EXAMPLE.answer}"
  },
  "vector": "[384-dim embedding — fastembed model]"
}`;

const LAYER_ROWS = [
  {
    layer: "Ontoloji (OWL)",
    when: "Yeni bilgi tipi / property gerektiğinde",
    example: "Değişmez — TrainingInteraction sınıfı zaten tanımlı",
    color: "#6366f1",
    store: "Fuseki graph/ontology",
  },
  {
    layer: "Knowledge Graph",
    when: "Her anlamlı öğrenme olayında",
    example: "TrainingInteraction triple'ları + hasTrainingEvent ilişkisi",
    color: "#22c55e",
    store: "Fuseki graph/assessment",
  },
  {
    layer: "PostgreSQL",
    when: "Her öğrenme olayında (source of truth)",
    example: "agent_learning_events: question_text + answer_text düz metin",
    color: "#3b82f6",
    store: "agent_learning_events",
  },
  {
    layer: "Vector DB (Qdrant)",
    when: "Metin retrieval gerektiğinde",
    example: 'documents: embed("Soru: …\\nYanıt: …") + workstream filtresi',
    color: "#a78bfa",
    store: "Qdrant documents",
  },
];

const bwBox: CSSProperties = {
  border: "2px solid #111",
  borderRadius: 4,
  padding: "8px 12px",
  background: "#fff",
  color: "#111",
  fontSize: 11,
  fontWeight: 600,
  textAlign: "center",
  lineHeight: 1.35,
};

const bwSub: CSSProperties = {
  fontSize: 9,
  fontWeight: 400,
  color: "#444",
  display: "block",
  marginTop: 2,
};

const bwDashed: CSSProperties = {
  ...bwBox,
  borderStyle: "dashed",
};

function Arrow({ label, dashed }: { label?: string; dashed?: boolean }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", color: "#111", fontSize: 9, padding: "2px 0" }}>
      <span style={{ fontSize: 14, lineHeight: 1 }}>↓</span>
      {label && (
        <span style={{ fontStyle: dashed ? "italic" : "normal", color: "#555" }}>{label}</span>
      )}
    </div>
  );
}

function SideArrow({ label }: { label: string }) {
  return (
    <span style={{ fontSize: 9, color: "#555", fontStyle: "italic", padding: "0 4px" }}>{label}</span>
  );
}

/** Siyah-beyaz zihinsel model — mermaid flowchart layout */
function MentalModelDiagram() {
  return (
    <div
      data-testid="mental-model-diagram"
      style={{
        background: "#f8f8f8",
        border: "2px solid #111",
        borderRadius: 8,
        padding: 16,
        color: "#111",
      }}
    >
      <p style={{ margin: "0 0 12px", textAlign: "center", fontSize: 12, fontWeight: 700, letterSpacing: "0.06em" }}>
        YAZMA — Eğitim
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 8, marginBottom: 4 }}>
        <div style={bwDashed}>
          Ontoloji OWL
          <span style={bwSub}>şema — nadiren</span>
        </div>
        <div style={bwBox}>
          AAHA
          <span style={bwSub}>soru-yanıt</span>
        </div>
        <div style={bwBox}>
          Metin
          <span style={bwSub}>bilgi girişi</span>
        </div>
        <div style={bwBox}>
          Döküman
          <span style={bwSub}>PDF / txt</span>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "#555", marginBottom: 4, paddingLeft: 4 }}>
        <span style={{ fontStyle: "italic" }}>şema tanımı ↘</span>
        <span>↓ her giriş</span>
      </div>

      <div style={{ maxWidth: 320, margin: "0 auto 4px" }}>
        <div style={{ ...bwBox, borderWidth: 3 }}>
          PostgreSQL
          <span style={bwSub}>agent_learning_events · source of truth</span>
        </div>
        <Arrow />
      </div>

      <p style={{ margin: "0 0 8px", textAlign: "center", fontSize: 10, fontWeight: 600, color: "#333" }}>
        Kayıt katmanları (paralel)
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, maxWidth: 480, margin: "0 auto 8px" }}>
        <div>
          <div style={bwBox}>
            Knowledge Graph
            <span style={bwSub}>Fuseki ABox</span>
          </div>
          <div style={{ display: "flex", justifyContent: "center", gap: 4, flexWrap: "wrap", marginTop: 4 }}>
            <SideArrow label="paralel ←" />
            <span style={{ fontSize: 9 }}>AAHA / Metin / Döküman</span>
          </div>
        </div>
        <div>
          <div style={bwBox}>
            Vector DB
            <span style={bwSub}>Qdrant documents</span>
          </div>
        </div>
      </div>

      <div style={{ borderTop: "2px dashed #999", margin: "16px 0 12px" }} />

      <p style={{ margin: "0 0 12px", textAlign: "center", fontSize: 12, fontWeight: 700, letterSpacing: "0.06em" }}>
        OKUMA — Çalışma zamanı
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, maxWidth: 520, margin: "0 auto", alignItems: "center" }}>
        <div style={bwBox}>
          Interview / Chat
          <span style={bwSub}>soru gelir</span>
        </div>
        <div style={{ textAlign: "center", fontSize: 16 }}>→</div>
        <div style={{ ...bwBox, borderWidth: 3 }}>
          Claude / LLM
          <span style={bwSub}>RAG context</span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, maxWidth: 400, margin: "12px auto 0" }}>
        <div style={{ textAlign: "center" }}>
          <span style={{ fontSize: 10, color: "#555" }}>↑ instance SPARQL</span>
          <div style={{ ...bwBox, marginTop: 4, fontSize: 10 }}>Knowledge Graph</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <span style={{ fontSize: 10, color: "#555" }}>↑ semantik arama</span>
          <div style={{ ...bwBox, marginTop: 4, fontSize: 10 }}>Vector DB</div>
        </div>
      </div>

      <p style={{ fontSize: 10, color: "#444", margin: "14px 0 0", textAlign: "center", lineHeight: 1.5 }}>
        Bilgi girişi → PG (her zaman) → KG + Qdrant (paralel) · Ontoloji şemayı tanımlar ·
        Soru gelince KG instance + Qdrant → LLM
      </p>
    </div>
  );
}

function CodeBlock({ title, lang, children }: { title: string; lang: string; children: string }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <strong style={{ fontSize: 11, color: "#e2e8f0" }}>{title}</strong>
        <span style={{ fontSize: 10, color: "#64748b" }}>{lang}</span>
      </div>
      <pre
        data-testid={`example-${lang}`}
        style={{
          margin: 0, padding: 12, borderRadius: 6, fontSize: 10, lineHeight: 1.45,
          background: "#0a0a0a", border: "1px solid #334155", color: "#a3e635",
          overflowX: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word",
        }}
      >
        {children}
      </pre>
    </div>
  );
}

function LayerBox({ title, subtitle, color, children }: {
  title: string;
  subtitle: string;
  color: string;
  children: ReactNode;
}) {
  return (
    <div style={{
      border: `1px solid ${color}44`, borderLeft: `4px solid ${color}`,
      borderRadius: 8, padding: 14, background: `${color}11`, marginBottom: 10,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
        <strong style={{ color, fontSize: 13 }}>{title}</strong>
        <span style={{ fontSize: 10, color: "#64748b" }}>{subtitle}</span>
      </div>
      {children}
    </div>
  );
}

export default function AgentKnowledgeArchitecture() {
  return (
    <div data-testid="agent-knowledge-architecture" style={{ fontSize: 13, color: "#cbd5e1", lineHeight: 1.55 }}>
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, margin: "0 0 8px", color: "#e2e8f0" }}>
          Knowledge Management — Best Practice Mimarisi
        </h2>
        <p style={{ margin: 0, color: "#94a3b8", fontSize: 12 }}>
          Agent öğrenmesi model ağırlığı değiştirmek değil; onaylanan bilgiyi katmanlara tutarlı yazmaktır.
        </p>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 13, fontWeight: 700, color: "#e2e8f0", margin: "0 0 12px", textAlign: "center" }}>
          Zihinsel Model
        </h3>
        <MentalModelDiagram />
      </section>

      <section style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 13, fontWeight: 700, color: "#e2e8f0", marginBottom: 12 }}>Katman sorumlulukları</h3>
        {LAYER_ROWS.map(row => (
          <LayerBox key={row.layer} title={row.layer} subtitle={row.store} color={row.color}>
            <p style={{ margin: "0 0 4px", fontSize: 11, color: "#94a3b8" }}>
              <strong style={{ color: "#e2e8f0" }}>Ne zaman:</strong> {row.when}
            </p>
            <p style={{ margin: 0, fontSize: 11, fontFamily: "monospace", color: "#94a3b8" }}>
              {row.example}
            </p>
          </LayerBox>
        ))}
      </section>

      <section
        data-testid="example-data-dumps"
        style={{
          background: "#0f1117", border: "1px solid #334155", borderRadius: 10, padding: 16, marginBottom: 20,
        }}
      >
        <h3 style={{ fontSize: 13, fontWeight: 700, color: "#4ade80", margin: "0 0 12px" }}>
          Örnek: Tam veri dökümü (kubernetes / AAHA)
        </h3>
        <div style={{ background: "#1a1525", borderRadius: 6, padding: 12, marginBottom: 16, fontSize: 12 }}>
          <p style={{ margin: "0 0 6px", color: "#a78bfa" }}>
            <strong>Soru:</strong> {EXAMPLE.question}
          </p>
          <p style={{ margin: "0 0 6px", color: "#e2e8f0" }}>
            <strong>Yanıt:</strong> {EXAMPLE.answer}
          </p>
          <p style={{ margin: 0, fontSize: 10, color: "#64748b" }}>
            event_id: <code style={{ color: "#94a3b8" }}>{EXAMPLE_EVENT_ID}</code>
          </p>
        </div>

        <CodeBlock title="1) PostgreSQL — SELECT ile göreceğiniz satır" lang="sql">
          {EXAMPLE_SQL}
        </CodeBlock>

        <CodeBlock title="2) Knowledge Graph — Fuseki'ye yazılan triple'lar" lang="turtle">
          {EXAMPLE_TURTLE}
        </CodeBlock>

        <CodeBlock title="3) Vector DB — Qdrant point payload" lang="json">
          {EXAMPLE_QDRANT}
        </CodeBlock>

        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, marginTop: 4 }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #334155", color: "#64748b", textAlign: "left" }}>
              <th style={{ padding: "6px 8px" }}>Katman</th>
              <th style={{ padding: "6px 8px" }}>Güncellendi mi?</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: "1px solid #1e293b" }}>
              <td style={{ padding: "8px", color: "#6366f1" }}>Ontoloji</td>
              <td style={{ padding: "8px", color: "#64748b" }}>Hayır (şema zaten var)</td>
            </tr>
            <tr style={{ borderBottom: "1px solid #1e293b" }}>
              <td style={{ padding: "8px", color: "#3b82f6" }}>PostgreSQL</td>
              <td style={{ padding: "8px", color: "#4ade80" }}>✓ Evet — düz metin soru + yanıt</td>
            </tr>
            <tr style={{ borderBottom: "1px solid #1e293b" }}>
              <td style={{ padding: "8px", color: "#22c55e" }}>Knowledge Graph</td>
              <td style={{ padding: "8px", color: "#4ade80" }}>✓ Evet — TrainingInteraction + hasTrainingEvent</td>
            </tr>
            <tr>
              <td style={{ padding: "8px", color: "#a78bfa" }}>Vector DB</td>
              <td style={{ padding: "8px", color: "#4ade80" }}>✓ Evet — Soru+Yanıt birleşik embed</td>
            </tr>
          </tbody>
        </table>
        <p style={{ fontSize: 11, color: "#64748b", marginTop: 12, marginBottom: 0 }}>
          Kayıt sonrası <code style={{ color: "#22c55e" }}>refersToConcept</code> ile domain kavramlarına link eklenir
          (LLM + keyword fallback). AI onaylı kayıtta <code style={{ color: "#a78bfa" }}>answer_author</code> = <strong>ai</strong>.
        </p>
      </section>

      <section style={{
        background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 16,
      }}>
        <h3 style={{ fontSize: 13, fontWeight: 700, color: "#e2e8f0", margin: "0 0 10px" }}>
          Bilgi girişi kontrol listesi
        </h3>
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "#94a3b8" }}>
          <li style={{ marginBottom: 6 }}>PostgreSQL kaydı oluşturuldu mu? (her zaman)</li>
          <li style={{ marginBottom: 6 }}>KG triple yazıldı mı? (AAHA, metin, döküman)</li>
          <li style={{ marginBottom: 6 }}>Qdrant embed yapıldı mı? (metin içeriği varsa)</li>
          <li style={{ marginBottom: 6 }}>Silme/güncelleme üç katmandan da yapıldı mı?</li>
          <li>Mevcut ontoloji yeterli mi? Değilse önce şemayı genişlet.</li>
        </ul>
      </section>
    </div>
  );
}
