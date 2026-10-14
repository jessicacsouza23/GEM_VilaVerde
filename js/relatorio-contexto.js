/* Complemento de ausências: não altera os registros nem a chamada do dia. */
(function () {
  const dataIso = valor => {
    const s = String(valor || '');
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
    const partes = s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    return partes ? `${partes[3]}-${partes[2]}-${partes[1]}` : '';
  };
  function paraAluna(historico, aluna, data, presenca) {
    if (!['Ausente', 'Justificada'].includes(presenca)) return null;
    const limite = dataIso(data);
    const registros = historico.filter(item => item.Aluna === aluna && dataIso(item.Data) && dataIso(item.Data) <= limite);
    const aulas = registros.filter(item => String(item.Tipo || '').startsWith('Analise_') && dataIso(item.Data) < limite);
    const ultimaData = aulas.map(item => dataIso(item.Data)).sort().at(-1);
    const ultimaAula = aulas.filter(item => dataIso(item.Data) === ultimaData);
    const casas = registros.filter(item => String(item.Tipo || '').startsWith('Casa_'));
    const recente = itens => [...itens].sort((a, b) => dataIso(b.Data).localeCompare(dataIso(a.Data)) || Number(b.id || 0) - Number(a.id || 0))[0];
    // Mesma regra de Minhas lições: novas lições substituem as anteriores
    // em métodos, MSA e Canto; apostilas e folhas avulsas acumulam pendências.
    const ultimaPratica = recente(casas.filter(item => item.Tipo.startsWith('Casa_Metodo_')));
    const msa = recente(casas.filter(item => item.Tipo === 'Casa_MSA'));
    const canto = recente(casas.filter(item => item.Tipo === 'Casa_Canto'));
    const resolvida = status => ['resolvido', 'realizada', 'realizadas - sem pendencia', 'realizada - sem pendencia', 'passou'].includes(String(status || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLowerCase());
    const pendentes = casas.filter(item => {
      if (resolvida(item.Status)) return false;
      if (item.Tipo.startsWith('Casa_Metodo_')) return dataIso(item.Data) === dataIso(ultimaPratica?.Data);
      if (item.Tipo === 'Casa_MSA') return item === msa;
      if (item.Tipo === 'Casa_Canto') return item === canto;
      return true;
    });
    return { ultimaAula, pendentes };
  }
  window.RelatorioContexto = { paraAluna };
})();
