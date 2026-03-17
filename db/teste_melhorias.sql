select intencao, motivo_fallback, count(*)
from conversas
where tipo_resposta='FALLBACK'
group by 1,2
order by count(*) desc;
