import PropTypes from 'prop-types'
import Typography from '@mui/material/Typography'

function DiagnosticView({ response, complete, error }) {
  return (
    <div>
      <div>
        <Typography variant="h6" component="span">
          Response:
        </Typography>
        <Typography variant="body">{JSON.stringify(response)}</Typography>
      </div>
      <div>
        <Typography variant="h6" component="span">
          Complete:
        </Typography>
        <Typography variant="body">{complete ? 'true' : 'false'}</Typography>
      </div>
      <div>
        <Typography variant="h6" component="span">
          Error:
        </Typography>
        <Typography variant="body">{error}</Typography>
      </div>
    </div>
  )
}

DiagnosticView.propTypes = {
  response: PropTypes.object.isRequired,
  complete: PropTypes.bool.isRequired,
  error: PropTypes.string.isRequired
}

export default DiagnosticView
