/**
 * View: Treinamento (placeholder elegante para onboarding futuro)
 */
const TrainingView = (() => {
    const COMING_FEATURES = [
        'Fluxo de onboarding guiado para novos tenants',
        'Quiz de configuração do perfil da prefeitura',
        'Importação assistida de FAQs e regulamentos municipais',
        'Métricas de qualidade das respostas do bot',
        'Sugestões automáticas de base de conhecimento',
        'Histórico de treinamentos e versões do RAG',
    ];

    function render(container) {
        container.innerHTML = `
      <div class="view-header">
        <h2 class="view-title">Treinamento</h2>
        <p class="view-sub">Módulo de onboarding e capacitação do tenant</p>
      </div>

      <div class="placeholder-area">
        <p class="placeholder-label">Próxima Versão</p>
        <h3 class="placeholder-title">Módulo de Treinamento</h3>
        <p class="placeholder-desc">
          Este módulo guiará o gestor municipal por um processo estruturado de configuração
          e validação do bot — do zero ao primeiro atendimento, sem necessidade de suporte técnico.
        </p>
        <ul class="placeholder-list">
          ${COMING_FEATURES.map(f => `<li>${f}</li>`).join('')}
        </ul>
      </div>

      <div class="card mt-16">
        <div class="card__title">ENQUANTO ISSO — CONFIGURE SUA BASE AGORA</div>
        <p style="font-size:13px;color:var(--steel-gray);margin-bottom:16px">
          Use a aba <strong>Base RAG</strong> para enviar documentos e treinar o bot imediatamente.
          Tipos aceitos: PDF, TXT, Markdown.
        </p>
        <button class="btn btn-ghost btn-mono" onclick="App.navigate('rag')">
          → ACESSAR BASE RAG
        </button>
      </div>
    `;
    }

    return { render };
})();
