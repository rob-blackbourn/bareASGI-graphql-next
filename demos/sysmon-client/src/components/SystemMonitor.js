import PropTypes from 'prop-types'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'

function SystemMonitor({ response, complete, error }) {
  const rows =
    response && response.data && response.data.latest
      ? response.data.latest.cpu.cores
      : response && response.data && response.data.system
      ? response.data.system.cpu.cores
      : []

  return (
    <TableContainer>
      <Table size="small" sx={{ maxWidth: 500 }}>
        <TableHead>
          <TableRow>
            <TableCell align="right">Percent</TableCell>
            <TableCell align="right">System</TableCell>
            <TableCell align="right">User</TableCell>
            <TableCell align="right">Idle</TableCell>
            <TableCell align="right">Nice</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map(row => (
            <TableRow key={row.core}>
              <TableCell align="right">{row.percent}</TableCell>
              <TableCell align="right">{row.times.system}</TableCell>
              <TableCell align="right">{row.times.user}</TableCell>
              <TableCell align="right">{row.times.idle}</TableCell>
              <TableCell align="right">{row.times.nice}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

SystemMonitor.propTypes = {
  response: PropTypes.object.isRequired,
  complete: PropTypes.bool.isRequired,
  error: PropTypes.string.isRequired
}

export default SystemMonitor
