import Accordion from '@mui/material/Accordion'
import AccordionSummary from '@mui/material/AccordionSummary'
import AccordionDetails from '@mui/material/AccordionDetails'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import Chip from '@mui/material/Chip'
import Box from '@mui/material/Box'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import BuildIcon from '@mui/icons-material/Build'
import type { Step } from './types'

interface StepsAccordionProps {
  steps: Step[]
}

export default function StepsAccordion({ steps }: StepsAccordionProps) {
  if (steps.length === 0) return null

  return (
    <Accordion
      disableGutters
      variant="outlined"
      sx={{ width: '100%', maxWidth: '75%', '&:before': { display: 'none' } }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          <BuildIcon fontSize="small" color="action" />
          <Typography variant="caption" color="text.secondary">
            {steps.length} étape{steps.length > 1 ? 's' : ''} d'exécution
          </Typography>
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Stack spacing={1.5}>
          {steps.map((step, index) => (
            <Box key={step.id}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 0.5 }}>
                <Chip label={`#${index + 1}`} size="small" />
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  {step.tool}
                </Typography>
              </Stack>
              <Typography
                variant="caption"
                component="pre"
                sx={{
                  m: 0,
                  fontFamily: 'monospace',
                  color: 'text.secondary',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all'
                }}
              >
                args: {JSON.stringify(step.args)}
              </Typography>
              <Typography
                variant="caption"
                component="p"
                sx={{ 
                  m: 0, 
                  color: 'text.secondary',
                  wordBreak: 'break-word' 
                }}
              >
                {formatResult(step.result)}
              </Typography>
            </Box>
          ))}
        </Stack>
      </AccordionDetails>
    </Accordion>
  )
}

function formatResult(result: string): string {
  if (!result) return ''
  
  const sourceRegex = /\[Source:\s*([^,]+),\s*ID:\s*([^\]]+)\]/g
  const matches = [...result.matchAll(sourceRegex)]
  
  if (matches.length > 0) {
    const uniqueSources = new Map<string, string>()
    for (const match of matches) {
      const file = match[1].trim()
      const id = match[2].trim()
      if (!uniqueSources.has(id)) {
        uniqueSources.set(id, file)
      }
    }
    
    const sourceStrings = Array.from(uniqueSources.entries()).map(
      ([id, file]) => `- ID: ${id}, Source: ${file}`
    )
    
    return `Sources trouvées : ${sourceStrings.join(' ')}`
  }
  
  if (result.length > 200) {
    return result.substring(0, 200) + '...'
  }
  return result
}
