import PropTypes from 'prop-types'
import Radio from '@mui/material/Radio'
import RadioGroup from '@mui/material/RadioGroup'
import FormControlLabel from '@mui/material/FormControlLabel'
import FormControl from '@mui/material/FormControl'
import FormLabel from '@mui/material/FormLabel'

function RequestComplexitySelector({ requestComplexity, handler }) {
  return (
    <FormControl component="fieldset">
      <FormLabel component="legend">Request Complexity</FormLabel>
      <RadioGroup
        aria-label="requestComplexity"
        name="request-complexity-radio-buttons-group"
        value={requestComplexity}
        onChange={handler}
      >
        <FormControlLabel value="simple" control={<Radio />} label="Simple" />
        <FormControlLabel value="complex" control={<Radio />} label="Complex" />
      </RadioGroup>
    </FormControl>
  )
}

RequestComplexitySelector.propTypes = {
  requestComplexity: PropTypes.string.isRequired,
  handler: PropTypes.func.isRequired
}

export default RequestComplexitySelector
