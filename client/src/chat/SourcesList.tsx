import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import Link from '@mui/material/Link'
import Tooltip from '@mui/material/Tooltip'
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import type { Source } from './types'

interface SourcesListProps {
  sources: Source[]
}

export default function SourcesList({ sources }: SourcesListProps) {
  if (sources.length === 0) return null

  return (
    <Stack spacing={0.5} sx={{ maxWidth: '75%' }}>
      <Typography variant="caption" color="text.secondary">
        Sources :
      </Typography>
      {sources.map((source) => (
        <Tooltip key={source.source_id} title={source.file.split('/').pop()} placement="top" arrow>
          <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
            <InsertDriveFileOutlinedIcon sx={{ fontSize: 14 }} color="disabled" />
            {source.url ? (
              <Link
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                variant="caption"
                sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.3 }}
              >
                {source.title}
                <OpenInNewIcon sx={{ fontSize: 12 }} />
              </Link>
            ) : (
              <Typography variant="caption">{source.title}</Typography>
            )}
          </Stack>
        </Tooltip>
      ))}
    </Stack>
  )
}
